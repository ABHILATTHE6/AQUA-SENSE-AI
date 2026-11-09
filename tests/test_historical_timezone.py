import json
from pathlib import Path

import pytest

from src.ingestion.historical_pipeline import ingest_historical_open_meteo
from src.ingestion.open_meteo_historical import HistoricalConfig, normalize_payload

FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_historical.json"


def payload_for_one_local_day():
    times = [f"2025-01-01T{hour:02d}:00" for hour in range(24)]
    return {
        "latitude": 15.8521,
        "longitude": 74.5045,
        "timezone": "Asia/Kolkata",
        "utc_offset_seconds": 19800,
        "hourly": {
            "time": times,
            "temperature_2m": [25.0] * 24,
            "relative_humidity_2m": [55.0] * 24,
            "precipitation": [0.0] * 24,
            "et0_fao_evapotranspiration": [0.2] * 24,
            "soil_moisture_0_to_7cm": [0.24] * 24,
        },
    }


def test_config_accepts_iana_timezone_and_uses_it_in_api_url():
    config = HistoricalConfig(
        "belagavi_city_pilot",
        15.8521,
        74.5045,
        "2025-01-01",
        "2025-12-31",
        timezone="Asia/Kolkata",
    )
    assert "timezone=Asia%2FKolkata" in config.url()


def test_config_rejects_unknown_iana_timezone():
    config = HistoricalConfig(
        "belagavi_city_pilot",
        15.8521,
        74.5045,
        "2025-01-01",
        "2025-01-02",
        timezone="Not/AZone",
    )
    with pytest.raises(ValueError, match="valid IANA timezone"):
        config.validate()


def test_local_naive_provider_times_are_not_mislabeled_as_utc():
    config = HistoricalConfig(
        "belagavi_city_pilot",
        15.8521,
        74.5045,
        "2025-01-01",
        "2025-01-01",
        timezone="Asia/Kolkata",
    )
    observations = normalize_payload(config, payload_for_one_local_day())
    assert observations[0]["observed_at"] == "2025-01-01T00:00:00+05:30"
    assert observations[5]["metadata"]["provider_timezone"] == "Asia/Kolkata"


def test_explicit_utc_timestamps_keep_their_instant():
    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2025-01-01", "2025-01-01"
    )
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    observations = normalize_payload(config, payload)
    assert observations[0]["observed_at"].endswith("Z")


def test_pipeline_aggregates_full_local_calendar_day(tmp_path):
    config = HistoricalConfig(
        "belagavi_city_pilot",
        15.8521,
        74.5045,
        "2025-01-01",
        "2025-01-01",
        timezone="Asia/Kolkata",
    )
    raw, hourly, daily, hourly_count, daily_count = ingest_historical_open_meteo(
        config,
        raw_root=tmp_path / "raw",
        processed_root=tmp_path / "processed",
        daily_root=tmp_path / "processed",
        fetcher=lambda _: payload_for_one_local_day(),
    )
    daily_rows = [json.loads(line) for line in daily.read_text(encoding="utf-8").splitlines()]
    assert raw.exists() and hourly.exists() and daily.exists()
    assert hourly_count == 24 * 5
    assert daily_count == 1
    assert daily_rows[0]["date"] == "2025-01-01"
    assert daily_rows[0]["calendar_timezone"] == "Asia/Kolkata"
    assert daily_rows[0]["rainfall_mm_sum"] == 0.0
