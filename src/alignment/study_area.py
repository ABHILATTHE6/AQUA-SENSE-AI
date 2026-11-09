"""Study-area and groundwater-station proximity readiness checks."""

from __future__ import annotations

from math import isclose
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.features.groundwater_alignment import haversine_km


def build_study_area_readiness_report(
    study_area: dict[str, Any],
    groundwater_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize candidate station proximity to a documented weather study point.

    This report is a discovery aid only. It never asserts that a station and
    weather grid point are scientifically equivalent or creates a join.
    """
    required = (
        "study_area_id", "name", "location_id", "latitude", "longitude",
        "timezone", "coordinate_source", "coordinate_source_url",
    )
    missing = [field for field in required if field not in study_area]
    if missing:
        raise ValueError(f"study area is missing required fields: {', '.join(missing)}")

    latitude = float(study_area["latitude"])
    longitude = float(study_area["longitude"])
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("study-area coordinates are outside valid ranges")
    try:
        ZoneInfo(str(study_area["timezone"]))
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown study-area timezone: {study_area['timezone']}") from exc

    radius = float(study_area.get("groundwater_station_candidate_radius_km", 15.0))
    if radius <= 0:
        raise ValueError("groundwater station candidate radius must be positive")

    stations: dict[str, tuple[float, float]] = {}
    missing_coordinates: set[str] = set()
    for index, record in enumerate(groundwater_records or [], start=1):
        station_id = str(record.get("location_id", "")).strip()
        if not station_id:
            raise ValueError(f"groundwater row {index} is missing location_id")
        metadata = record.get("metadata") or {}
        lat, lon = metadata.get("latitude"), metadata.get("longitude")
        if lat is None or lon is None:
            missing_coordinates.add(station_id)
            continue
        lat, lon = float(lat), float(lon)
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            missing_coordinates.add(station_id)
            continue
        existing = stations.get(station_id)
        if existing and (
            not isclose(existing[0], lat, abs_tol=0.0001)
            or not isclose(existing[1], lon, abs_tol=0.0001)
        ):
            raise ValueError(f"conflicting coordinates for station {station_id}")
        stations[station_id] = (lat, lon)

    candidates = []
    for station_id, (station_lat, station_lon) in stations.items():
        distance = haversine_km(latitude, longitude, station_lat, station_lon)
        candidates.append({
            "station_location_id": station_id,
            "station_latitude": station_lat,
            "station_longitude": station_lon,
            "distance_from_study_area_km": round(distance, 3),
            "within_discovery_radius": distance <= radius,
            "status": (
                "nearby_station_requires_manual_review"
                if distance <= radius else "outside_discovery_radius"
            ),
        })
    candidates.sort(key=lambda row: row["distance_from_study_area_km"])

    return {
        "report_version": "1.0",
        "study_area": {
            "study_area_id": study_area["study_area_id"],
            "name": study_area["name"],
            "location_id": study_area["location_id"],
            "latitude": latitude,
            "longitude": longitude,
            "timezone": study_area["timezone"],
            "coordinate_source": study_area["coordinate_source"],
            "coordinate_source_url": study_area["coordinate_source_url"],
            "coordinate_semantics": study_area.get("coordinate_semantics"),
        },
        "weather_configuration": {
            "provider": study_area.get("weather_provider", "Open-Meteo Historical Weather API"),
            "model": study_area.get("weather_model", "era5"),
            "nominal_resolution_km": study_area.get("nominal_weather_resolution_km"),
            "grid_note": (
                "A model grid estimate is not a site observation; requested coordinates "
                "may be mapped/downscaled to a provider grid cell."
            ),
        },
        "groundwater_station_audit": {
            "station_count_with_coordinates": len(stations),
            "station_count_without_valid_coordinates": len(missing_coordinates),
            "candidate_radius_km": radius,
            "nearby_station_count": sum(row["within_discovery_radius"] for row in candidates),
            "stations": candidates,
            "stations_without_valid_coordinates": sorted(missing_coordinates),
        },
        "automatic_join_performed": False,
        "readiness_status": (
            "station_candidates_need_manual_review" if candidates
            else "waiting_for_groundwater_station_records"
        ),
        "limitations": study_area.get("limitations", []),
        "interpretation": (
            "This is a spatial discovery audit only. Review station identity, datum, "
            "local aquifer relevance, weather-grid support, elevation and timestamps "
            "before any temporal or spatial join."
        ),
    }
