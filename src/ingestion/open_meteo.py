"""Open-Meteo weather ingestion and normalization for AQUA-SENSE AI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.ingestion.base import RawRecord, utc_now
from src.validation.observation import validate_observation

API_URL = "https://api.open-meteo.com/v1/forecast"
SOURCE_ID = "open_meteo"

CANONICAL_MAPPING = {
    "precipitation": ("rainfall_mm", "mm"),
    "temperature_2m": ("air_temperature_c", "degC"),
    "relative_humidity_2m": ("relative_humidity_pct", "pct"),
    "et0_fao_evapotranspiration": ("et0_mm", "mm"),
    "soil_moisture_0_to_1cm": ("soil_moisture_m3_m3", "m3/m3"),
}

DEFAULT_HOURLY_VARIABLES = tuple(CANONICAL_MAPPING)


class OpenMeteoError(RuntimeError):
    """Raised for provider/network/response-shape failures."""


@dataclass(frozen=True)
class OpenMeteoConfig:
    """Parameters required to retrieve a forecast for one project location."""

    location_id: str
    latitude: float
    longitude: float
    forecast_days: int = 3
    timezone: str = "UTC"

    def query_params(self) -> dict[str, str]:
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        if not 1 <= self.forecast_days <= 16:
            raise ValueError("forecast_days must be between 1 and 16")
        if not self.location_id.strip():
            raise ValueError("location_id must be non-empty")
        if self.timezone != "UTC":
            raise ValueError("AQUA-SENSE ingestion currently requires timezone=UTC")
        return {
            "latitude": f"{self.latitude:.6f}",
            "longitude": f"{self.longitude:.6f}",
            "hourly": ",".join(DEFAULT_HOURLY_VARIABLES),
            "forecast_days": str(self.forecast_days),
            "timezone": self.timezone,
        }

    def url(self) -> str:
        return f"{API_URL}?{urlencode(self.query_params())}"


def _decode_json(response: Any) -> dict[str, Any]:
    try:
        payload = json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenMeteoError("Open-Meteo returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise OpenMeteoError("Open-Meteo response must be a JSON object")
    if payload.get("error") is True:
        reason = payload.get("reason", "unknown provider error")
        raise OpenMeteoError(f"Open-Meteo error: {reason}")
    return payload


def fetch_payload(
    config: OpenMeteoConfig,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Fetch a provider-native forecast payload without transforming it."""

    request = Request(
        config.url(),
        headers={"Accept": "application/json", "User-Agent": "aqua-sense-ai/0.1"},
    )
    try:
        with opener(request, timeout=30) as response:
            return _decode_json(response)
    except HTTPError as exc:
        raise OpenMeteoError(f"Open-Meteo HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise OpenMeteoError(f"Open-Meteo network error: {exc.reason}") from exc


def to_raw_record(
    config: OpenMeteoConfig,
    payload: dict[str, Any],
    retrieved_at: datetime | None = None,
) -> RawRecord:
    """Wrap the untouched provider response with ingestion provenance."""

    return RawRecord(
        source_id=SOURCE_ID,
        retrieved_at=retrieved_at or utc_now(),
        payload=payload,
        source_location=config.location_id,
    )


def _validate_hourly_shape(payload: dict[str, Any]) -> tuple[list[str], dict[str, list[Any]]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise OpenMeteoError("Open-Meteo response is missing an hourly object")
    times = hourly.get("time")
    if not isinstance(times, list) or not times:
        raise OpenMeteoError("Open-Meteo response is missing hourly.time")

    variables: dict[str, list[Any]] = {}
    for provider_field in CANONICAL_MAPPING:
        values = hourly.get(provider_field)
        if not isinstance(values, list):
            raise OpenMeteoError(f"Open-Meteo response is missing hourly.{provider_field}")
        if len(values) != len(times):
            raise OpenMeteoError(
                f"hourly.{provider_field} has {len(values)} values for {len(times)} timestamps"
            )
        variables[provider_field] = values
    return [str(value) for value in times], variables


def _observation_id(location_id: str, variable: str, timestamp: str) -> str:
    safe_time = timestamp.replace(":", "").replace("-", "")
    return f"open_meteo:{location_id}:{safe_time}:{variable}"


def normalize_payload(
    config: OpenMeteoConfig,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert provider hourly arrays into validated canonical observations."""

    times, variables = _validate_hourly_shape(payload)
    latitude = payload.get("latitude", config.latitude)
    longitude = payload.get("longitude", config.longitude)
    timezone = payload.get("timezone", config.timezone)
    observations: list[dict[str, Any]] = []

    for index, raw_time in enumerate(times):
        observed_at = raw_time if raw_time.endswith("Z") else f"{raw_time}Z"
        for provider_field, (variable, unit) in CANONICAL_MAPPING.items():
            value = variables[provider_field][index]
            if value is None:
                continue
            observation = {
                "observation_id": _observation_id(config.location_id, variable, raw_time),
                "observed_at": observed_at,
                "location_id": config.location_id,
                "source": SOURCE_ID,
                "variable": variable,
                "value": value,
                "unit": unit,
                "quality_flag": "estimated",
                "latitude": latitude,
                "longitude": longitude,
                "metadata": {
                    "provider_field": provider_field,
                    "provider_timezone": timezone,
                    "provider_elevation_m": payload.get("elevation"),
                    "forecast": True,
                },
            }
            validate_observation(observation)
            observations.append(observation)
    return observations


@dataclass(frozen=True)
class OpenMeteoAdapter:
    """SourceAdapter implementation for the Open-Meteo forecast API."""

    config: OpenMeteoConfig
    source_id: str = SOURCE_ID

    def fetch(self, **_: Any) -> Iterable[RawRecord]:
        payload = fetch_payload(self.config)
        yield to_raw_record(self.config, payload)
