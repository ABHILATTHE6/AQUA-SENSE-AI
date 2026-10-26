import pytest

from src.scoring.water_stress import StressConfig, score_water_stress


def daily(rainfall, soil, et0, temperature):
    return {
        "date": "2026-09-01",
        "location_id": "demo_location",
        "rainfall_mm_sum": rainfall,
        "soil_moisture_m3_m3_mean": soil,
        "et0_mm_sum": et0,
        "air_temperature_c_mean": temperature,
    }


def test_dry_hot_conditions_score_higher_than_wet_cool_conditions():
    dry = score_water_stress(daily(0.0, 0.08, 8.0, 40.0))
    wet = score_water_stress(daily(15.0, 0.42, 1.0, 18.0))
    assert dry["water_stress_index"] > wet["water_stress_index"]
    assert dry["water_stress_index"] == 100.0
    assert wet["water_stress_index"] == 0.0
    assert dry["water_stress_category"] == "very_high"
    assert wet["water_stress_category"] == "low"


def test_score_is_bounded_and_exposes_explanation_components():
    result = score_water_stress(daily(5.0, 0.25, 5.0, 30.0))
    assert 0.0 <= result["water_stress_index"] <= 100.0
    assert set(result["component_scores"]) == {
        "rainfall_deficit",
        "soil_moisture_deficit",
        "evaporative_demand",
        "heat",
    }
    assert result["method"] == "rule_based_v1"


@pytest.mark.parametrize(
    "record",
    [
        daily(-1.0, 0.2, 4.0, 25.0),
        daily(2.0, 1.2, 4.0, 25.0),
        daily(2.0, 0.2, -1.0, 25.0),
        daily(None, 0.2, 4.0, 25.0),
        daily(2.0, 0.2, 4.0, float("nan")),
    ],
)
def test_invalid_inputs_are_rejected(record):
    with pytest.raises(ValueError):
        score_water_stress(record)


def test_invalid_weights_are_rejected():
    config = StressConfig(rainfall_weight=0.5)
    with pytest.raises(ValueError, match="sum to 1.0"):
        score_water_stress(daily(1.0, 0.2, 4.0, 25.0), config)
