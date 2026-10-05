"""Historical Open-Meteo reanalysis ingestion for AQUA-SENSE AI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.ingestion.base import RawRecord, utc_now

API_URL = "https://archive-api.open-meteo.com/v1/archive"
SOURCE_ID = "open_meteo"

HISTORICAL_HOURLY_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "et0_fao_evapotranspiration",
    "soil_moisture_0_to_7cm",
)

CANONICAL_MAPPING = {
    "precipitation": ("rainfall_mm", "mm"),
    "temperature_2m": ("air_temperature_c", "degC"),
    "relative_humidity_2m": ("relative_humidity_pct", "pct"),
    "et0_fao_evapotranspiration": ("et0_mm", "mm"),
    "soil_moisture_0_to_7cm": ("soil_moisture_m3_m3", "m3/m3"),
}


class OpenMeteoHistoricalError(RuntimeError):
    """Raised for historical-provider/network/response-shape failures."""


@dataclass(frozen=True)
class HistoricalConfig:
    """Parameters for one bounded historical weather extraction."""

    location_id: str
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    timezone: str = "UTC"
    model: str = "era5"
    max_days: int = 366

    def validate(self) -> None:
        if not self.location_id.strip():
            raise ValueError("location_id must be non-empty")
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        try:
            start = date.fromisoformat(self.start_date)
            end = date.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ValueError("start_date and end_date must use YYYY-MM-DD") from exc
        if end < start:
            raise ValueError("end_date must be on or after start_date")
        if (end - start).days + 1 > self.max_days:
            raise ValueError(f"historical request cannot exceed {self.max_days} days")
        if self.timezone != "UTC":
            raise ValueError("AQUA-SENSE historical ingestion currently requires timezone=UTC")
        if not self.model.strip():
            raise ValueError("model must be non-empty")

    def query_params(self) -> dict[str, str]:
        self.validate()
        return {
            "latitude": f"{self.latitude:.6f}",
            "longitude": f"{self.longitude:.6f}",
            "start_date": self.start_date,
            "end_date": self.end_date,
            "hourly": ",".join(HISTORICAL_HOURLY_VARIABLES),
            "timezone": self.timezone,
            "temperature_unit": "celsius",
            "precipitation_unit": "mm",
            "timeformat": "iso8601",
            "models": self.model,
        }

    def url(self) -> str:
        return f"{API_URL}?{urlencode(self.query_params())}"


def _decode_json(response: Any) -> dict[str, Any]:
    try:
        payload = json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenMeteoHistoricalError("Open-Meteo historical response is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise OpenMeteoHistoricalError("Open-Meteo historical response must be a JSON object")
    if payload.get("error") is True:
        raise OpenMeteoHistoricalError(
            f"Open-Meteo historical error: {payload.get('reason', 'unknown provider error')}"
        )
    return payload


def fetch_payload(
    config: HistoricalConfig,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Fetch one provider-native historical payload without transformation."""

    request = Request(
        config.url(),
        headers={"Accept": "application/json", "User-Agent": "aqua-sense-ai/0.1"},
    )
    try:
        with opener(request, timeout=60) as response:
            return _decode_json(response)
    except HTTPError as exc:
        raise OpenMeteoHistoricalError(f"Open-Meteo historical HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise OpenMeteoHistoricalError(
            f"Open-Meteo historical network error: {exc.reason}"
        ) from exc


def to_raw_record(
    config: HistoricalConfig,
    payload: dict[str, Any],
    retrieved_at: datetime | None = None,
) -> RawRecord:
    """Wrap the untouched reanalysis payload with provenance."""

    return RawRecord(
        source_id=SOURCE_ID,
        retrieved_at=retrieved_at or utc_now(),
        payload=payload,
        source_location=config.location_id,
    )


def _validate_hourly_shape(payload: dict[str, Any]) -> tuple[list[str], dict[str, list[Any]]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise OpenMeteoHistoricalError("response is missing hourly object")

    times = hourly.get("time")
    if not isinstance(times, list) or not times:
        raise OpenMeteoHistoricalError("response is missing hourly.time")

    variables: dict[str, list[Any]] = {}
    for field in HISTORICAL_HOURLY_VARIABLES:
        values = hourly.get(field)
        if not isinstance(values, list):
            raise OpenMeteoHistoricalError(f"response is missing hourly.{field}")
        if len(values) != len(times):
            raise OpenMeteoHistoricalError(
                f"hourly.{field} has {len(values)} values for {len(times)} timestamps"
            )
        variables[field] = values
    return [str(value) for value in times], variables


def _observation_id(location_id: str, variable: str, timestamp: str) -> str:
    safe_time = timestamp.replace(":", "").replace("-", "")
    return f"open_meteo:{location_id}:{safe_time}:{variable}"


def normalize_payload(config: HistoricalConfig, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert hourly reanalysis arrays into canonical observations."""

    times, variables = _validate_hourly_shape(payload)
    latitude = payload.get("latitude", config.latitude)
    longitude = payload.get("longitude", config.longitude)
    provider_timezone = payload.get("timezone", config.timezone)
    observations: list[dict[str, Any]] = []

    for index, raw_time in enumerate(times):
        observed_at = raw_time if raw_time.endswith("Z") else f"{raw_time}Z"
        for provider_field, (variable, unit) in CANONICAL_MAPPING.items():
            value = variables[provider_field][index]
            if value is None:
                continue
            observations.append(
                {
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
                        "provider_timezone": provider_timezone,
                        "reanalysis_model": config.model,
                        "historical": True,
                    },
                }
            )
    return observations
