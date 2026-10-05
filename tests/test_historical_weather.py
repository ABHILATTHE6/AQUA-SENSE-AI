import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ingestion.open_meteo_historical import (
    HistoricalConfig,
    OpenMeteoHistoricalError,
    fetch_payload,
    normalize_payload,
    to_raw_record,
)

FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_historical.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_historical_url_contains_date_and_model_contract():
    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2026-09-01", "2026-09-30"
    )
    url = config.url()
    assert "archive-api.open-meteo.com/v1/archive?" in url
    assert "start_date=2026-09-01" in url
    assert "end_date=2026-09-30" in url
    assert "models=era5" in url
    assert "soil_moisture_0_to_7cm" in url


def test_config_rejects_unbounded_date_range():
    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2025-01-01", "2026-12-31"
    )
    with pytest.raises(ValueError, match="cannot exceed 366 days"):
        config.validate()


def test_normalize_historical_payload_preserves_five_canonical_variables():
    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2026-09-01", "2026-09-01"
    )
    observations = normalize_payload(config, load_fixture())
    assert len(observations) == 15
    assert {item["variable"] for item in observations} == {
        "rainfall_mm",
        "air_temperature_c",
        "relative_humidity_pct",
        "et0_mm",
        "soil_moisture_m3_m3",
    }
    assert all(item["quality_flag"] == "estimated" for item in observations)
    assert all(item["metadata"]["historical"] is True for item in observations)


def test_mismatched_arrays_are_rejected():
    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2026-09-01", "2026-09-01"
    )
    payload = load_fixture()
    payload["hourly"]["precipitation"] = [0.0]
    with pytest.raises(OpenMeteoHistoricalError, match="3 timestamps"):
        normalize_payload(config, payload)


def test_raw_record_retains_reanalysis_provenance():
    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2026-09-01", "2026-09-01"
    )
    timestamp = datetime(2026, 10, 5, tzinfo=timezone.utc)
    record = to_raw_record(config, load_fixture(), timestamp)
    assert record.source_id == "open_meteo"
    assert record.source_location == "demo_location"
    assert record.retrieved_at == timestamp


def test_fetch_payload_uses_historical_endpoint_without_network():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return FIXTURE.read_bytes()

    def fake_opener(request, timeout):
        assert request.full_url.startswith("https://archive-api.open-meteo.com/v1/archive?")
        assert timeout == 60
        return FakeResponse()

    config = HistoricalConfig(
        "demo_location", 20.5937, 78.9629, "2026-09-01", "2026-09-01"
    )
    payload = fetch_payload(config, opener=fake_opener)
    assert payload["hourly"]["time"][0] == "2026-09-01T00:00"
