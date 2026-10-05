from src.features.daily_weather import aggregate_daily


def _hour(day: str, hour: int, variable: str, value: float):
    units = {
        "rainfall_mm": "mm",
        "air_temperature_c": "degC",
        "relative_humidity_pct": "pct",
        "et0_mm": "mm",
        "soil_moisture_m3_m3": "m3/m3",
    }
    return {
        "observation_id": f"test:{day}:{hour}:{variable}",
        "observed_at": f"{day}T{hour:02d}:00:00Z",
        "location_id": "demo_location",
        "source": "open_meteo",
        "variable": variable,
        "value": value,
        "unit": units[variable],
        "quality_flag": "estimated",
        "latitude": 20.5937,
        "longitude": 78.9629,
    }


def test_daily_aggregation_sums_fluxes_and_averages_states():
    variables = [
        ("rainfall_mm", 1.0),
        ("air_temperature_c", 20.0),
        ("relative_humidity_pct", 50.0),
        ("et0_mm", 0.5),
        ("soil_moisture_m3_m3", 0.3),
    ]
    rows = [
        _hour("2026-09-01", hour, variable, value)
        for hour in range(24)
        for variable, value in variables
    ]

    result = aggregate_daily(rows)
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
        _hour("2026-09-01", hour, variable, value)
        for hour in range(23)
        for variable, value in variables
    ]
    assert aggregate_daily(rows) == []
