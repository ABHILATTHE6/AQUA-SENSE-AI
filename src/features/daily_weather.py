"""Deterministic daily aggregation from canonical hourly observations."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any

from src.validation.observation import validate_observation


class DailyAggregationError(ValueError):
    """Raised when hourly observations cannot form a valid daily record."""


def _date_key(timestamp: str) -> str:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise DailyAggregationError(f"invalid observation timestamp: {timestamp}") from exc


def aggregate_daily(
    observations: list[dict[str, Any]],
    *,
    expected_hours: int = 24,
) -> list[dict[str, Any]]:
    """Aggregate complete hourly observations into daily model inputs.

    Rainfall and ET0 are summed; temperature, humidity and soil moisture are averaged.
    Days missing any expected hourly variable are excluded rather than silently imputed.
    """

    if expected_hours <= 0:
        raise ValueError("expected_hours must be positive")

    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    locations: dict[str, tuple[str, float | None, float | None, str]] = {}

    for observation in observations:
        validate_observation(observation)
        day = _date_key(observation["observed_at"])
        variable = observation["variable"]
        grouped[day][variable].append(float(observation["value"]))
        locations[day] = (
            observation["location_id"],
            observation.get("latitude"),
            observation.get("longitude"),
            observation["source"],
        )

    required = {
        "rainfall_mm",
        "air_temperature_c",
        "relative_humidity_pct",
        "et0_mm",
        "soil_moisture_m3_m3",
    }
    output: list[dict[str, Any]] = []

    for day in sorted(grouped):
        values = grouped[day]
        if any(len(values.get(variable, [])) != expected_hours for variable in required):
            continue

        location_id, latitude, longitude, source = locations[day]
        output.append(
            {
                "date": day,
                "location_id": location_id,
                "source": source,
                "rainfall_mm_sum": round(sum(values["rainfall_mm"]), 4),
                "air_temperature_c_mean": round(mean(values["air_temperature_c"]), 4),
                "relative_humidity_pct_mean": round(mean(values["relative_humidity_pct"]), 4),
                "et0_mm_sum": round(sum(values["et0_mm"]), 4),
                "soil_moisture_m3_m3_mean": round(mean(values["soil_moisture_m3_m3"]), 6),
                "latitude": latitude,
                "longitude": longitude,
                "complete_hourly_day": True,
                "aggregation": "sum_for_flux_mean_for_state",
            }
        )

    return output
