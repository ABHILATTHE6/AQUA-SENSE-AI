from src.evaluation.sensitivity import build_sensitivity_report, compare_scores
from src.scoring.water_stress import score_dataset


def weather_rows(days=10):
    rows = []
    for day in range(1, days + 1):
        rows.append({
            "date": f"2026-09-{day:02d}",
            "location_id": "demo_location",
            "rainfall_mm_sum": 0.5 if day < 6 else 12.0,
            "soil_moisture_m3_m3_mean": 0.12 if day < 6 else 0.36,
            "et0_mm_sum": 7.0 if day < 6 else 2.5,
            "air_temperature_c_mean": 37.0 if day < 6 else 24.0,
        })
    return rows


def test_report_discloses_missing_ground_truth_and_scenarios():
    report = build_sensitivity_report(weather_rows())
    assert report["ground_truth_available"] is False
    assert report["predictive_accuracy_assessed"] is False
    assert report["accuracy_metrics"] is None
    assert report["baseline_summary"]["count"] == 10
    assert {row["scenario_id"] for row in report["scenarios"]} == {
        "baseline_v1", "equal_weights", "soil_moisture_emphasis",
        "atmospheric_demand_emphasis", "tighter_upper_thresholds",
    }
    assert report["time_aware_analysis"]["available"] is True
    assert set(report["time_aware_analysis"]["partitions"]) == {"train", "validation", "test"}


def test_comparing_configuration_with_itself_has_zero_shift():
    scores = score_dataset(weather_rows(3))
    result = compare_scores(scores, scores)
    assert result["mean_absolute_score_shift"] == 0.0
    assert result["max_absolute_score_shift"] == 0.0
    assert result["category_changes"] == 0
    assert result["category_change_rate_pct"] == 0.0


def test_short_period_gets_clear_unavailable_temporal_status():
    report = build_sensitivity_report(weather_rows(2))
    assert report["time_aware_analysis"]["available"] is False
    assert "three unique dates" in report["time_aware_analysis"]["reason"]


def test_duplicate_input_observations_are_rejected():
    rows = weather_rows(3)
    rows.append(dict(rows[0]))
    try:
        build_sensitivity_report(rows)
    except ValueError as exc:
        assert "duplicate date/location" in str(exc)
    else:
        raise AssertionError("expected duplicate date/location validation")
