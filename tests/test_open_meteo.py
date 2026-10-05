import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ingestion.base import RawRecord
from src.ingestion.open_meteo import (
    OpenMeteoAdapter,
    OpenMeteoConfig,
    OpenMeteoError,
    fetch_payload,
    normalize_payload,
    to_raw_record,
)

FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_forecast.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_url_contains_explicit_query_contract():
    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629, forecast_days=3)
    url = config.url()
    assert "latitude=20.593700" in url
    assert "longitude=78.962900" in url
    assert "forecast_days=3" in url
    assert "temperature_2m" in url
    assert "soil_moisture_0_to_1cm" in url


def test_normalize_payload_creates_canonical_observations():
    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629)
    observations = normalize_payload(config, load_fixture())

    assert len(observations) == 10
    assert {row["variable"] for row in observations} == {
        "rainfall_mm",
        "air_temperature_c",
        "relative_humidity_pct",
        "et0_mm",
        "soil_moisture_m3_m3",
    }
    assert all(row["quality_flag"] == "estimated" for row in observations)
    assert all(row["observed_at"].endswith("Z") for row in observations)


def test_normalize_payload_validates_each_observation():
    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629)
    payload = load_fixture()
    payload["hourly"]["relative_humidity_2m"][1] = 140
    with pytest.raises(ValueError, match="relative_humidity_pct must be <= 100"):
        normalize_payload(config, payload)


def test_mismatched_provider_arrays_are_rejected():
    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629)
    payload = load_fixture()
    payload["hourly"]["precipitation"] = [0.0]
    with pytest.raises(OpenMeteoError, match="2 timestamps"):
        normalize_payload(config, payload)


def test_raw_record_preserves_provider_payload():
    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629)
    payload = load_fixture()
    retrieved_at = datetime(2026, 10, 5, tzinfo=timezone.utc)
    record = to_raw_record(config, payload, retrieved_at)

    assert isinstance(record, RawRecord)
    assert record.source_id == "open_meteo"
    assert record.payload == payload
    assert record.retrieved_at == retrieved_at


def test_adapter_implements_source_contract_without_network(monkeypatch):
    payload = load_fixture()
    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629)

    monkeypatch.setattr("src.ingestion.open_meteo.fetch_payload", lambda _: payload)
    adapter = OpenMeteoAdapter(config)
    records = list(adapter.fetch())

    assert adapter.source_id == "open_meteo"
    assert len(records) == 1
    assert records[0].payload == payload


def test_fetch_payload_accepts_provider_response_without_network():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return FIXTURE.read_bytes()

    def fake_opener(request, timeout):
        assert request.full_url.startswith("https://api.open-meteo.com/v1/forecast?")
        assert timeout == 30
        return FakeResponse()

    config = OpenMeteoConfig("demo_location", 20.5937, 78.9629)
    payload = fetch_payload(config, opener=fake_opener)
    assert payload["hourly"]["time"][0] == "2026-10-05T00:00"
