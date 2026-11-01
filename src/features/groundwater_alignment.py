"""Groundwater daily summaries and conservative weather-point matching."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import asin, cos, isclose, radians, sin, sqrt
from statistics import mean, median
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.validation.reference_target import validate_reference_target

EARTH_RADIUS_KM = 6371.0088


def aggregate_groundwater_daily(
    records: list[dict[str, Any]],
    *,
    timezone_name: str = "Asia/Kolkata",
    expected_observations_per_day: int = 4,
    minimum_observations: int = 3,
) -> list[dict[str, Any]]:
    """Summarize observed station readings by local date, without imputation.

    Four observations/day is a configurable expectation for a six-hourly source,
    not a strict guarantee. Incomplete days remain in the result with a status flag.
    """
    if expected_observations_per_day < 1:
        raise ValueError("expected_observations_per_day must be positive")
    if not 1 <= minimum_observations <= expected_observations_per_day:
        raise ValueError("minimum_observations must be between 1 and expected_observations_per_day")
    try:
        target_zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone_name}") from exc

    grouped: dict[tuple[str, str], list[tuple[datetime, float]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    coordinates: dict[str, tuple[float | None, float | None]] = {}

    for index, record in enumerate(records, start=1):
        validate_reference_target(record)
        if record["source"] != "karnataka_groundwater":
            raise ValueError(f"row {index} is not from karnataka_groundwater")
        if record["target_variable"] != "groundwater_depth_m":
            raise ValueError(f"row {index} is not a groundwater_depth_m reference")
        observed = datetime.fromisoformat(str(record["observed_at"]).replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise ValueError(f"row {index} observed_at must include a timezone")
        local_time = observed.astimezone(target_zone)
        location_id = str(record["location_id"])
        duplicate_key = (location_id, local_time.isoformat())
        if duplicate_key in seen:
            raise ValueError(f"duplicate station/timestamp observation for {location_id}")
        seen.add(duplicate_key)

        metadata = record.get("metadata") or {}
        latitude = metadata.get("latitude")
        longitude = metadata.get("longitude")
        point = (
            float(latitude) if latitude is not None else None,
            float(longitude) if longitude is not None else None,
        )
        previous = coordinates.get(location_id)
        if previous is None:
            coordinates[location_id] = point
        else:
            for old, new in zip(previous, point):
                if old is not None and new is not None and not isclose(old, new, abs_tol=0.0001):
                    raise ValueError(f"station coordinates changed within location_id {location_id}")
                if old is None and new is not None:
                    coordinates[location_id] = point

        grouped[(location_id, local_time.date().isoformat())].append(
            (local_time, float(record["value"]))
        )

    summaries: list[dict[str, Any]] = []
    for (location_id, day), pairs in sorted(grouped.items()):
        pairs.sort(key=lambda pair: pair[0])
        depths = [pair[1] for pair in pairs]
        count = len(depths)
        latitude, longitude = coordinates[location_id]
        summaries.append({
            "location_id": location_id,
            "date": day,
            "source": "karnataka_groundwater",
            "target_variable": "groundwater_depth_m",
            "unit": "m",
            "summary_method": "mean_median_min_max_latest_of_observed_readings",
            "mean_depth_m": round(mean(depths), 4),
            "median_depth_m": round(median(depths), 4),
            "minimum_depth_m": round(min(depths), 4),
            "maximum_depth_m": round(max(depths), 4),
            "latest_depth_m": round(depths[-1], 4),
            "observation_count": count,
            "expected_observations_per_day": expected_observations_per_day,
            "observation_count_coverage_pct": round(
                min(100.0, 100.0 * count / expected_observations_per_day), 2
            ),
            "excess_observation_count": max(0, count - expected_observations_per_day),
            "first_observation_local": pairs[0][0].isoformat(),
            "last_observation_local": pairs[-1][0].isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "daily_summary_status": (
                "sufficient_observations" if count >= minimum_observations
                else "insufficient_observations"
            ),
            "minimum_observations_required": minimum_observations,
            "timezone": timezone_name,
            "reference_status": "candidate_not_approved",
            "interpretation": (
                "Daily station summary of observed groundwater depth; not a direct "
                "label for surface soil moisture, crop stress, or the composite index."
            ),
        })
    return summaries


def haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Great-circle distance between two latitude/longitude coordinate pairs."""
    for label, latitude, longitude in (
        ("first", lat_a, lon_a), ("second", lat_b, lon_b)
    ):
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError(f"{label} coordinates are outside valid ranges")
    phi_a, phi_b = radians(lat_a), radians(lat_b)
    delta_phi = radians(lat_b - lat_a)
    delta_lambda = radians(lon_b - lon_a)
    term = sin(delta_phi / 2) ** 2 + cos(phi_a) * cos(phi_b) * sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(min(1.0, term)))


def _coordinate(value: Any, lower: float, upper: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if lower <= number <= upper else None


def build_station_weather_candidates(
    groundwater_records: list[dict[str, Any]],
    weather_locations: list[dict[str, Any]],
    *,
    maximum_distance_km: float = 10.0,
    ambiguity_margin_km: float = 1.0,
) -> list[dict[str, Any]]:
    """Audit nearby weather points; do not automatically join station observations."""
    if maximum_distance_km <= 0:
        raise ValueError("maximum_distance_km must be positive")
    if ambiguity_margin_km < 0:
        raise ValueError("ambiguity_margin_km cannot be negative")

    weather: list[dict[str, Any]] = []
    seen_weather_ids: set[str] = set()
    for index, location in enumerate(weather_locations, start=1):
        location_id = location.get("location_id")
        if not isinstance(location_id, str) or not location_id.strip():
            raise ValueError(f"weather location {index} requires location_id")
        location_id = location_id.strip()
        if location_id in seen_weather_ids:
            raise ValueError(f"duplicate weather location_id: {location_id}")
        seen_weather_ids.add(location_id)
        lat = _coordinate(location.get("latitude"), -90, 90)
        lon = _coordinate(location.get("longitude"), -180, 180)
        if lat is None or lon is None:
            raise ValueError(f"weather location {location_id} has invalid coordinates")
        weather.append({"location_id": location_id, "latitude": lat, "longitude": lon})

    stations: dict[str, tuple[float | None, float | None]] = {}
    for record in groundwater_records:
        location_id = str(record.get("location_id", "")).strip()
        if not location_id:
            raise ValueError("groundwater records require location_id")
        metadata = record.get("metadata") or {}
        point = (
            _coordinate(metadata.get("latitude"), -90, 90),
            _coordinate(metadata.get("longitude"), -180, 180),
        )
        previous = stations.get(location_id)
        if previous is None or previous == (None, None):
            stations[location_id] = point
        elif point == (None, None):
            continue
        elif previous != point:
            raise ValueError(f"conflicting station coordinates for {location_id}")

    results: list[dict[str, Any]] = []
    for station_id, (latitude, longitude) in sorted(stations.items()):
        if latitude is None or longitude is None:
            results.append({
                "station_location_id": station_id,
                "match_status": "missing_station_coordinates",
                "candidate_weather_location_id": None,
                "nearest_distance_km": None,
                "alternatives": [],
                "automatic_join_performed": False,
            })
            continue
        ranked = sorted(
            (
                haversine_km(latitude, longitude, point["latitude"], point["longitude"]),
                point,
            )
            for point in weather
        )
        if not ranked:
            status, candidate, nearest, alternatives = (
                "no_weather_locations", None, None, []
            )
        else:
            nearest_distance, nearest_point = ranked[0]
            alternatives = [
                {"weather_location_id": item["location_id"], "distance_km": round(distance, 3)}
                for distance, item in ranked[:3]
            ]
            nearest = round(nearest_distance, 3)
            if nearest_distance > maximum_distance_km:
                status, candidate = "outside_maximum_distance", None
            elif len(ranked) > 1 and ranked[1][0] - nearest_distance < ambiguity_margin_km:
                status, candidate = "ambiguous_nearest_location", None
            else:
                status, candidate = "candidate_nearest_location", nearest_point["location_id"]
        results.append({
            "station_location_id": station_id,
            "match_status": status,
            "candidate_weather_location_id": candidate,
            "nearest_distance_km": nearest,
            "maximum_distance_km": maximum_distance_km,
            "ambiguity_margin_km": ambiguity_margin_km,
            "alternatives": alternatives,
            "automatic_join_performed": False,
        })
    return results
