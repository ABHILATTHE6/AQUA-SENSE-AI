import json
from pathlib import Path

from src.ingestion.historical_pipeline import ingest_historical_open_meteo
from src.ingestion.open_meteo_historical import HistoricalConfig

FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_historical.json"


def test_historical_pipeline_persists_three_layers(tmp_path):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    raw, hourly, daily, hourly_count, daily_count = ingest_historical_open_meteo(
        HistoricalConfig(
            "demo_location", 20.5937, 78.9629, "2026-09-01", "2026-09-01"
        ),
        raw_root=tmp_path / "raw",
        processed_root=tmp_path / "processed",
        daily_root=tmp_path / "processed",
        fetcher=lambda config: payload,
    )

    assert raw.exists()
    assert hourly.exists()
    assert daily.exists()
    assert hourly_count == 15
    assert daily_count == 0
