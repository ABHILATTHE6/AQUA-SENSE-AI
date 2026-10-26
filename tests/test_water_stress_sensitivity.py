from src.evaluation.sensitivity import build_sensitivity_report, compare_scores
from src.scoring.water_stress import score_dataset


def weather_rows(days=10):
    rows = []
    for day in range(1, days + 1):
        rows.append(
            {
                "date": f"2026-09-{day:02d}",
                "location_id": "demo_location",
                "rainfall_mm_sum": 0.5 if day < 6 else 12.0,
                "soil_moisture_m3_m3_mean": 0.12 if day < 6 else 0.36,
                "et0_mm_sum": 7.0 if day < 6 else 2.5,
                "air_temperature_c_mean": 37.0 if day < 6 else 24.0,
            }
        )
    return rows


def test_report_discloses_no_ground_truth_and_includes_sensitivity_scenarios():
    report = build_sensitivity_report(weather_rows())
    assert report["ground_truth_available"] is False
    assert report["predictive_accuracy_assessed"] is False
    assert report["accuracy_metrics"] is None
    assert report["baseline_summary"]["count"] == 10
    scenario_ids = {item["scenario_id"] for item in report["scenarios"]}
    assert scenario_ids == {
        "baseline_v1",
        "equal_weights",
        "soil_moisture_emphasis",
        "atmospheric_demand_emphasis",
        "tighter_upper_thresholds",
    }
    assert report["time_aware_analysis"]["available"] is True
    assert set(report["time_aware_analysis"]["partitions"]) == {
        "train", "validation", "test"
    }


def test_default_scenario_matches_itself_without_category_changes():
    rows = weather_rows(3)
    scores = score_dataset(rows)
    result = compare_scores(scores, scores)
    assert result["mean_absolute_score_shift"] == 0.0
    assert result["max_absolute_score_shift"] == 0.0
    assert result["category_changes"] == 0
    assert result["category_change_rate_pct"] == 0.0


def test_report_gracefully_marks_short_date_window_as_unavailable():
    report = build_sensitivity_report(weather_rows(2))
    assert report["time_aware_analysis"]["available"] is False
    assert "three unique dates" in report["time_aware_analysis"]["reason"]
