from datetime import datetime, timedelta, timezone

import pytest

from src.features.daily_weather import DailyAggregationError, aggregate_daily


def _hour(timestamp: str, variable: str, value: float, location_id: str = "demo_location"):
    units = {
        "rainfall_mm": "mm",
        "air_temperature_c": "degC",
        "relative_humidity_pct": "pct",
        "et0_mm": "mm",
        "soil_moisture_m3_m3": "m3/m3",
    }
    return {
        "observation_id": f"test:{timestamp}:{variable}:{location_id}",
        "observed_at": timestamp,
        "location_id": location_id,
        "source": "open_meteo",
        "variable": variable,
        "value": value,
        "unit": units[variable],
        "quality_flag": "estimated",
        "latitude": 20.5937,
        "longitude": 78.9629,
    }


def _full_day_rows(day: str, location_id: str = "demo_location"):
    variables = [
        ("rainfall_mm", 1.0),
        ("air_temperature_c", 20.0),
        ("relative_humidity_pct", 50.0),
        ("et0_mm", 0.5),
        ("soil_moisture_m3_m3", 0.3),
    ]
    return [
        _hour(f"{day}T{hour:02d}:00:00Z", variable, value, location_id)
        for hour in range(24)
        for variable, value in variables
    ]


def test_daily_aggregation_sums_fluxes_and_averages_states():
    result = aggregate_daily(_full_day_rows("2026-09-01"))
    assert len(result) == 1
    daily = result[0]
    assert daily["rainfall_mm_sum"] == 24.0
    assert daily["et0_mm_sum"] == 12.0
    assert daily["air_temperature_c_mean"] == 20.0
    assert daily["relative_humidity_pct_mean"] == 50.0
    assert daily["soil_moisture_m3_m3_mean"] == 0.3


def test_incomplete_day_is_excluded_instead_of_imputed():
    variables = [
        ("rainfall_mm", 0.0),
        ("air_temperature_c", 20.0),
        ("relative_humidity_pct", 50.0),
        ("et0_mm", 0.5),
        ("soil_moisture_m3_m3", 0.3),
    ]
    rows = [
        _hour(f"2026-09-01T{hour:02d}:00:00Z", variable, value)
        for hour in range(23)
        for variable, value in variables
    ]
    assert aggregate_daily(rows) == []


def test_timezone_option_groups_by_local_calendar_day():
    variables = [
        ("rainfall_mm", 1.0),
        ("air_temperature_c", 20.0),
        ("relative_humidity_pct", 50.0),
        ("et0_mm", 0.5),
        ("soil_moisture_m3_m3", 0.3),
    ]
    start = datetime(2026, 9, 1, 18, 30, tzinfo=timezone.utc)
    rows = [
        _hour((start + timedelta(hours=offset)).isoformat(), variable, value)
        for offset in range(24)
        for variable, value in variables
    ]
    result = aggregate_daily(rows, timezone_name="Asia/Kolkata")
    assert len(result) == 1
    assert result[0]["date"] == "2026-09-02"
    assert result[0]["calendar_timezone"] == "Asia/Kolkata"


def test_daily_aggregation_keeps_distinct_locations_separate():
    rows = _full_day_rows("2026-09-01", "site-a") + _full_day_rows("2026-09-01", "site-b")
    result = aggregate_daily(rows)
    assert len(result) == 2
    assert {row["location_id"] for row in result} == {"site-a", "site-b"}


def test_timezone_aggregation_requires_aware_timestamps_and_valid_zone():
    row = _full_day_rows("2026-09-01")[0]
    row["observed_at"] = "2026-09-01T00:00:00"
    with pytest.raises(DailyAggregationError, match="timezone-aware"):
        aggregate_daily([row], timezone_name="Asia/Kolkata")
    with pytest.raises(DailyAggregationError, match="unknown aggregation timezone"):
        aggregate_daily(_full_day_rows("2026-09-01"), timezone_name="Invalid/Timezone")
