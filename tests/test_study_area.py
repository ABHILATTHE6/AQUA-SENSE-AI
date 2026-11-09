import json
from pathlib import Path

import pytest

from src.alignment.study_area import build_study_area_readiness_report

CONFIG = Path(__file__).parents[1] / "config" / "study_areas.json"


def belagavi_area():
    return json.loads(CONFIG.read_text(encoding="utf-8"))["study_areas"]["belagavi_city_pilot"]


def station(location_id, latitude, longitude):
    return {
        "location_id": location_id,
        "metadata": {"latitude": latitude, "longitude": longitude},
    }


def test_belagavi_study_area_has_documented_coordinates_and_local_timezone():
    area = belagavi_area()
    report = build_study_area_readiness_report(area)
    assert report["study_area"]["latitude"] == 15.8521
    assert report["study_area"]["longitude"] == 74.5045
    assert report["study_area"]["timezone"] == "Asia/Kolkata"
    assert report["weather_configuration"]["model"] == "era5"
    assert report["automatic_join_performed"] is False
    assert report["readiness_status"] == "waiting_for_groundwater_station_records"


def test_nearby_groundwater_station_is_candidate_for_manual_review():
    area = belagavi_area()
    report = build_study_area_readiness_report(
        area,
        [station("station-near", 15.86, 74.51)],
    )
    audit = report["groundwater_station_audit"]
    assert audit["nearby_station_count"] == 1
    assert audit["stations"][0]["status"] == "nearby_station_requires_manual_review"
    assert report["automatic_join_performed"] is False


def test_distant_and_missing_station_coordinates_are_reported_separately():
    report = build_study_area_readiness_report(
        belagavi_area(),
        [
            station("station-far", 13.0, 77.0),
            station("station-no-coordinates", None, None),
        ],
    )
    audit = report["groundwater_station_audit"]
    assert audit["nearby_station_count"] == 0
    assert audit["stations"][0]["status"] == "outside_discovery_radius"
    assert audit["stations_without_valid_coordinates"] == ["station-no-coordinates"]


def test_conflicting_coordinates_for_same_station_are_rejected():
    with pytest.raises(ValueError, match="conflicting coordinates"):
        build_study_area_readiness_report(
            belagavi_area(),
            [
                station("station-a", 15.86, 74.51),
                station("station-a", 15.90, 74.55),
            ],
        )


def test_invalid_timezone_and_coordinates_are_rejected():
    area = belagavi_area()
    invalid_timezone = dict(area, timezone="Not/AZone")
    with pytest.raises(ValueError, match="unknown study-area timezone"):
        build_study_area_readiness_report(invalid_timezone)
    invalid_coordinates = dict(area, latitude=100.0)
    with pytest.raises(ValueError, match="outside valid ranges"):
        build_study_area_readiness_report(invalid_coordinates)
