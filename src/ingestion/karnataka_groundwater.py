"""Normalization helpers for Karnataka groundwater telemetry CSV exports.

Provider-native CSVs remain immutable; outputs are candidate reference records,
never automatically approved ground truth.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SOURCE_ID = "karnataka_groundwater"
SOURCE_DATASET_URL = (
    "https://nwdp.nwic.gov.in/en/dataset/"
    "ground-water-level-telemetry-hourly-karnataka-ground-water-department"
)
SOURCE_DOWNLOAD_URL = (
    "https://nwdp.nwic.gov.in/dataset/832fa98a-93d2-4f5b-8c4a-28964b4993db/"
    "resource/f6178453-cbc0-4005-98b3-8408e6dfc19a/download/"
    "gwl_tel_6_hourly_karnataka_gw_ka_2021_2025.csv"
)
DEFAULT_SOURCE_TIMEZONE = "Asia/Kolkata"


def normalize_header(value: str) -> str:
    """Make a CSV header comparable despite punctuation and whitespace."""
    return "".join(char.lower() for char in str(value) if char.isalnum())


def _column_name(
    fieldnames: list[str], aliases: tuple[str, ...], required: bool = True
) -> str | None:
    by_normalized = {
        normalize_header(name): name for name in fieldnames if name is not None
    }
    for alias in aliases:
        actual = by_normalized.get(normalize_header(alias))
        if actual is not None:
            return actual
    if required:
        raise ValueError(
            f"required CSV column not found; expected one of: {', '.join(aliases)}"
        )
    return None


def resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    """Resolve required and optional source fields from portal CSV headers."""
    if not fieldnames or any(name is None for name in fieldnames):
        raise ValueError("CSV header is empty or malformed")
    return {
        "timestamp": _column_name(fieldnames, (
            "Data Acquisition Time", "Timestamp", "Observation Time", "Date Time"
        )),
        "depth": _column_name(fieldnames, (
            "Groundwater Level Telemetry 6 Hourly (meter)",
            "Groundwater Level Telemetry Hourly (meter)",
            "Groundwater Level (m)", "Groundwater Depth (m)", "GWL (m)"
        )),
        "station": _column_name(fieldnames, ("Station", "Station Name", "Well Name")),
        "record_id": _column_name(
            fieldnames, ("_id", "SlNo", "Serial Number", "Record ID"), required=False
        ),
        "agency": _column_name(fieldnames, ("Agency", "Data Provider"), required=False),
        "state": _column_name(fieldnames, ("State",), required=False),
        "district": _column_name(fieldnames, ("District",), required=False),
        "tehsil": _column_name(fieldnames, ("Tehsil", "Taluk", "Taluka"), required=False),
        "block": _column_name(fieldnames, ("Block",), required=False),
        "village": _column_name(fieldnames, ("Village",), required=False),
        "basin": _column_name(fieldnames, ("Basin",), required=False),
        "latitude": _column_name(fieldnames, ("Latitude", "Lat"), required=False),
        "longitude": _column_name(fieldnames, ("Longitude", "Lon", "Long"), required=False),
        "elevation": _column_name(
            fieldnames, ("RL_MSL", "Elevation", "Reduced Level MSL"), required=False
        ),
    }


def _parse_timestamp(raw_value: str, timezone_name: str) -> datetime:
    text = raw_value.strip()
    if not text:
        raise ValueError("missing observation timestamp")
    try:
        source_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown source timezone: {timezone_name}") from exc

    normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        value = datetime.fromisoformat(normalized)
    except ValueError:
        value = None
        for fmt in (
            "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
            "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
        ):
            try:
                value = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        if value is None:
            raise ValueError(f"unrecognized observation timestamp: {raw_value!r}")
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=source_timezone)
    return value


def _parse_required_float(raw_value: Any, field: str) -> float:
    if raw_value is None or not str(raw_value).strip():
        raise ValueError(f"missing {field}")
    try:
        value = float(str(raw_value).strip().replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"{field} is not numeric: {raw_value!r}") from exc
    if not isfinite(value):
        raise ValueError(f"{field} must be finite")
    return value


def _optional_float(raw_value: Any) -> float | None:
    if raw_value is None or not str(raw_value).strip():
        return None
    try:
        value = float(str(raw_value).strip().replace(",", ""))
    except ValueError:
        return None
    return value if isfinite(value) else None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def normalize_groundwater_row(
    row: dict[str, Any],
    *,
    row_number: int,
    fieldnames: list[str],
    source_timezone: str = DEFAULT_SOURCE_TIMEZONE,
    source_url: str = SOURCE_DOWNLOAD_URL,
    column_mapping: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """Normalize a provider row into the reference-target contract.

    Naive timestamps use the supplied timezone (default Asia/Kolkata). Verify
    that assumption against provider documentation before scientific analysis.
    Invalid or missing measurements raise ValueError for quarantine by the caller.
    """
    columns = column_mapping or resolve_columns(fieldnames)
    timestamp_raw = row.get(columns["timestamp"]) if columns["timestamp"] else None
    depth_raw = row.get(columns["depth"]) if columns["depth"] else None
    station_raw = row.get(columns["station"]) if columns["station"] else None
    station = str(station_raw or "").strip()
    if not station:
        raise ValueError("missing station identifier/name")

    observed_at = _parse_timestamp(str(timestamp_raw or ""), source_timezone)
    depth = _parse_required_float(depth_raw, "groundwater depth")
    if depth < 0:
        raise ValueError("groundwater depth must be non-negative for this target contract")

    def raw_value(key: str) -> str | None:
        column = columns.get(key)
        value = row.get(column) if column else None
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    state = raw_value("state") or "Karnataka"
    district = raw_value("district") or "unknown-district"
    latitude = _optional_float(raw_value("latitude"))
    longitude = _optional_float(raw_value("longitude"))
    if latitude is not None and not -90 <= latitude <= 90:
        latitude = None
    if longitude is not None and not -180 <= longitude <= 180:
        longitude = None
    location_material = "-".join(part for part in (state, district, station) if part)
    location_id = "kgw-" + (_slug(location_material) or "unknown-station")
    if len(location_id) > 120:
        location_id = location_id[:120].rstrip("-")

    source_record_id = raw_value("record_id") or f"csv-row-{row_number}"
    identity_material = "|".join(
        (source_record_id, station, observed_at.isoformat(), str(depth))
    )
    digest = hashlib.sha256(identity_material.encode("utf-8")).hexdigest()[:32]
    metadata = {
        "provider": "Karnataka Ground Water Department (Karnataka GW label in NWDP)",
        "dataset_url": SOURCE_DATASET_URL,
        "download_url": source_url,
        "source_row_number": row_number,
        "agency": raw_value("agency"),
        "state": state,
        "district": raw_value("district"),
        "tehsil": raw_value("tehsil"),
        "block": raw_value("block"),
        "village": raw_value("village"),
        "basin": raw_value("basin"),
        "latitude": latitude,
        "longitude": longitude,
        "elevation_msl_m": _optional_float(raw_value("elevation")),
        "source_timestamp_text": str(timestamp_raw or "").strip(),
        "source_timezone_assumption": source_timezone,
    }
    return {
        "reference_id": f"kgw-{digest}",
        "source_record_id": source_record_id,
        "observed_at": observed_at.isoformat(),
        "location_id": location_id,
        "source": SOURCE_ID,
        "target_variable": "groundwater_depth_m",
        "value": depth,
        "unit": "m",
        "temporal_support": "instantaneous",
        "spatial_support": {"kind": "point", "spatial_id": location_id},
        "quality_flag": "observed",
        "independence_assessment": {
            "status": "candidate",
            "notes": (
                "Public state groundwater telemetry candidate. Independent source does not "
                "make it a direct label for daily surface-soil or crop water stress; target "
                "relevance, station metadata, timestamp timezone, and alignment require review."
            ),
        },
        "metadata": metadata,
    }
