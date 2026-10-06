from src.quality.daily_profile import profile_daily_dataset, quality_flags


def row(day: str, rainfall: float = 5.0):
    return {
        "date": day,
        "location_id": "demo_location",
        "complete_hourly_day": True,
        "rainfall_mm_sum": rainfall,
        "air_temperature_c_mean": 25.0,
        "relative_humidity_pct_mean": 60.0,
        "et0_mm_sum": 4.0,
        "soil_moisture_m3_m3_mean": 0.30,
    }


def test_profile_detects_duplicate_dates_and_calendar_gaps():
    profile = profile_daily_dataset([
        row("2026-09-01"),
        row("2026-09-03"),
        row("2026-09-03", rainfall=6.0),
    ])
    assert profile["row_count"] == 3
    assert profile["duplicate_date_count"] == 1
    assert profile["missing_calendar_day_count"] == 1
    assert "duplicate_dates" in quality_flags(profile)
    assert "calendar_gaps" in quality_flags(profile)


def test_profile_reports_numeric_distribution():
    profile = profile_daily_dataset([row("2026-09-01", rainfall=2.0), row("2026-09-02", rainfall=4.0)])
    summary = profile["numeric"]["rainfall_mm_sum"]
    assert summary["count"] == 2
    assert summary["mean"] == 3.0
