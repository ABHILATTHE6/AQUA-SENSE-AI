import json
import sys

import pytest

from scripts.prepare_groundwater_alignment import main
from src.features.groundwater_alignment import (
    aggregate_groundwater_daily,
    build_station_weather_candidates,
    haversine_km,
)


def reference_record(timestamp, depth, *, location="well-a", latitude=12.3, longitude=76.6):
    return {
        "reference_id": f"ref-{timestamp}-{depth}",
        "observed_at": timestamp,
        "location_id": location,
        "source": "karnataka_groundwater",
        "target_variable": "groundwater_depth_m",
        "value": depth,
        "unit": "m",
        "temporal_support": "instantaneous",
        "spatial_support": {"kind": "point", "spatial_id": location},
        "quality_flag": "observed",
        "independence_assessment": {
            "status": "candidate",
            "notes": "Candidate groundwater context; not a composite-index label.",
        },
        "metadata": {"latitude": latitude, "longitude": longitude},
    }


def test_daily_summary_uses_india_local_calendar_and_retains_statistics():
    rows = [
        reference_record(f"2025-01-01T{hour:02d}:00:00+05:30", depth)
        for hour, depth in ((0, 8.4), (6, 8.2), (12, 8.1), (18, 8.0))
    ]
    result = aggregate_groundwater_daily(rows)
    assert len(result) == 1
    day = result[0]
    assert day["date"] == "2025-01-01"
    assert day["observation_count"] == 4
    assert day["observation_count_coverage_pct"] == 100.0
    assert day["mean_depth_m"] == 8.175
    assert day["latest_depth_m"] == 8.0
    assert day["daily_summary_status"] == "sufficient_observations"
    assert day["reference_status"] == "candidate_not_approved"


def test_utc_times_cross_into_next_india_local_day():
    rows = [
        reference_record(f"2025-01-01T{hour:02d}:00:00+00:00", 5.0)
        for hour in (20, 22, 23)
    ]
    result = aggregate_groundwater_daily(rows, minimum_observations=2)
    assert result[0]["date"] == "2025-01-02"
    assert result[0]["daily_summary_status"] == "sufficient_observations"


def test_incomplete_day_is_retained_and_flagged_not_imputed():
    rows = [
        reference_record(f"2025-01-01T{hour:02d}:00:00+05:30", 6.0)
        for hour in (0, 12)
    ]
    result = aggregate_groundwater_daily(rows)
    assert result[0]["observation_count"] == 2
    assert result[0]["observation_count_coverage_pct"] == 50.0
    assert result[0]["daily_summary_status"] == "insufficient_observations"


def test_duplicate_timestamps_and_wrong_source_are_rejected():
    record = reference_record("2025-01-01T06:00:00+05:30", 5.0)
    with pytest.raises(ValueError, match="duplicate station/timestamp"):
        aggregate_groundwater_daily([record, dict(record)])
    invalid = dict(record, source="open_meteo")
    with pytest.raises(ValueError, match="not from karnataka_groundwater"):
        aggregate_groundwater_daily([invalid])


def test_station_coordinate_changes_are_rejected():
    first = reference_record("2025-01-01T06:00:00+05:30", 5.0)
    second = reference_record(
        "2025-01-01T12:00:00+05:30", 5.1, latitude=13.0
    )
    with pytest.raises(ValueError, match="coordinates changed"):
        aggregate_groundwater_daily([first, second])


def test_haversine_identical_points_is_zero():
    assert haversine_km(12.3, 76.6, 12.3, 76.6) == 0.0


def test_nearest_weather_location_is_reported_as_candidate_only():
    rows = [reference_record("2025-01-01T06:00:00+05:30", 5.0)]
    weather = [
        {"location_id": "near", "latitude": 12.305, "longitude": 76.605},
        {"location_id": "far", "latitude": 12.8, "longitude": 77.0},
    ]
    result = build_station_weather_candidates(rows, weather)
    assert result[0]["match_status"] == "candidate_nearest_location"
    assert result[0]["candidate_weather_location_id"] == "near"
    assert result[0]["automatic_join_performed"] is False


def test_ambiguous_weather_points_are_not_selected():
    rows = [reference_record("2025-01-01T06:00:00+05:30", 5.0)]
    weather = [
        {"location_id": "a", "latitude": 12.301, "longitude": 76.6},
        {"location_id": "b", "latitude": 12.302, "longitude": 76.6},
    ]
    result = build_station_weather_candidates(rows, weather)
    assert result[0]["match_status"] == "ambiguous_nearest_location"
    assert result[0]["candidate_weather_location_id"] is None


def test_far_and_missing_coordinates_are_separately_reported():
    rows = [
        reference_record("2025-01-01T06:00:00+05:30", 5.0, location="far-well"),
        reference_record("2025-01-01T06:00:00+05:30", 5.0, location="no-coords", latitude=None, longitude=None),
    ]
    result = build_station_weather_candidates(
        rows,
        [{"location_id": "weather", "latitude": 20.5, "longitude": 78.9}],
        maximum_distance_km=5,
    )
    states = {row["station_location_id"]: row["match_status"] for row in result}
    assert states["far-well"] == "outside_maximum_distance"
    assert states["no-coords"] == "missing_station_coordinates"


def test_invalid_weather_coordinates_and_conflicting_station_points_fail():
    with pytest.raises(ValueError, match="invalid coordinates"):
        build_station_weather_candidates(
            [reference_record("2025-01-01T06:00:00+05:30", 5.0)],
            [{"location_id": "bad", "latitude": 200, "longitude": 70}],
        )
    with pytest.raises(ValueError, match="conflicting station coordinates"):
        build_station_weather_candidates(
            [
                reference_record("2025-01-01T06:00:00+05:30", 5.0),
                reference_record("2025-01-01T12:00:00+05:30", 5.1, latitude=13.0),
            ],
            [{"location_id": "weather", "latitude": 12.3, "longitude": 76.6}],
        )


def test_prepare_cli_writes_daily_and_spatial_audit_outputs(tmp_path, monkeypatch, capsys):
    source = tmp_path / "observations.jsonl"
    weather = tmp_path / "weather.json"
    daily = tmp_path / "daily.jsonl"
    report_path = tmp_path / "alignment.json"
    rows = [
        reference_record(f"2025-01-01T{hour:02d}:00:00+05:30", depth)
        for hour, depth in ((0, 8.4), (6, 8.2), (12, 8.1), (18, 8.0))
    ]
    source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    weather.write_text(json.dumps({
        "near": {"latitude": 12.305, "longitude": 76.605}
    }), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "prepare_groundwater_alignment.py",
        "--input", str(source),
        "--weather-locations", str(weather),
        "--daily-output", str(daily),
        "--report", str(report_path),
    ])
    assert main() == 0
    daily_rows = [json.loads(line) for line in daily.read_text(encoding="utf-8").splitlines()]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(daily_rows) == 1
    assert report["spatial_candidate_matching"]["automatic_join_performed"] is False
    assert "No weather join was performed" in capsys.readouterr().out
