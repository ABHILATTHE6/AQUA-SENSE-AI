from src.features.lagged import add_leakage_safe_features


def row(day: int, rainfall: float, temperature: float):
    return {
        "date": f"2026-09-{day:02d}",
        "location_id": "demo_location",
        "source": "open_meteo",
        "rainfall_mm_sum": rainfall,
        "air_temperature_c_mean": temperature,
        "relative_humidity_pct_mean": 60.0,
        "et0_mm_sum": 4.0,
        "soil_moisture_m3_m3_mean": 0.30,
        "complete_hourly_day": True,
    }


def test_lags_use_exact_prior_calendar_day():
    rows = add_leakage_safe_features([
        row(1, 1.0, 20.0),
        row(2, 100.0, 21.0),
    ])
    assert rows[1]["rainfall_mm_sum_lag_1d"] == 1.0


def test_rolling_feature_excludes_current_day():
    rows = add_leakage_safe_features([
        row(day, 1.0, 20.0) for day in range(1, 9)
    ])
    assert rows[7]["rainfall_mm_sum_rolling_sum_7d"] == 7.0
    assert rows[7]["rainfall_mm_sum_rolling_7d"] == 1.0


def test_missing_calendar_day_prevents_false_rolling_window():
    rows = add_leakage_safe_features([
        row(1, 1.0, 20.0),
        row(2, 1.0, 20.0),
        row(4, 1.0, 20.0),
    ])
    assert rows[2]["rainfall_mm_sum_lag_3d"] is None
    assert rows[2]["rainfall_mm_sum_rolling_3d"] is None
