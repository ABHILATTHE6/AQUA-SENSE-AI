import pytest

from src.ingestion.karnataka_groundwater import normalize_groundwater_row
from src.quality.karnataka_groundwater import KarnatakaGroundwaterProfile

HEADERS = [
    "_id", "Station", "State", "District", "Latitude", "Longitude",
    "Data Acquisition Time", "Groundwater Level Telemetry 6 Hourly (meter)",
]


def row(record_id, station, timestamp, depth, district="Mysuru", lat="12.3", lon="76.6"):
    return {
        "_id": record_id,
        "Station": station,
        "State": "Karnataka",
        "District": district,
        "Latitude": lat,
        "Longitude": lon,
        "Data Acquisition Time": timestamp,
        "Groundwater Level Telemetry 6 Hourly (meter)": str(depth),
    }


def test_duplicate_station_timestamp_is_flagged_not_silently_written():
    profile = KarnatakaGroundwaterProfile()
    first = normalize_groundwater_row(
        row("1", "Well A", "2025-01-01 06:00:00", 5.0),
        row_number=1, fieldnames=HEADERS,
    )
    duplicate = normalize_groundwater_row(
        row("2", "Well A", "2025-01-01 06:00:00", 5.1),
        row_number=2, fieldnames=HEADERS,
    )
    profile.begin_row()
    profile.accept(first)
    profile.begin_row()
    with pytest.raises(ValueError, match="duplicate station/timestamp"):
        profile.accept(duplicate)
    profile.reject("duplicate station/timestamp observation")
    report = profile.to_dict()
    assert report["row_counts"]["accepted_rows"] == 1
    assert report["row_counts"]["rejected_rows"] == 1
    assert report["row_counts"]["duplicate_station_timestamps"] == 1


def test_missing_coordinates_are_counted_for_manual_review():
    record = normalize_groundwater_row(
        row("1", "Well A", "2025-01-01 06:00:00", 5.0, lat="", lon=""),
        row_number=1, fieldnames=HEADERS,
    )
    profile = KarnatakaGroundwaterProfile()
    profile.begin_row()
    profile.accept(record)
    report = profile.to_dict()
    assert report["coverage"]["rows_missing_coordinates"] == 1
    assert report["coverage"]["coordinate_completeness_pct"] == 0.0
