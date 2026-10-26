import json

from src.scoring.water_stress import score_dataset


def test_dataset_scoring_preserves_rows_and_metadata():
    rows = [
        {
            "date": "2026-09-01",
            "location_id": "demo_location",
            "rainfall_mm_sum": 1.0,
            "soil_moisture_m3_m3_mean": 0.12,
            "et0_mm_sum": 7.0,
            "air_temperature_c_mean": 38.0,
        }
    ]
    result = score_dataset(rows)
    assert len(result) == 1
    assert result[0]["date"] == rows[0]["date"]
    assert result[0]["location_id"] == rows[0]["location_id"]
    assert "weighted_contributions" in result[0]
