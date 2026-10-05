import json
from pathlib import Path

from src.ingestion.open_meteo import OpenMeteoConfig
from src.ingestion.pipeline import ingest_open_meteo

FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_forecast.json"


def test_ingest_pipeline_writes_raw_and_processed_layers(tmp_path):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def fake_fetch(config):
        return payload

    raw_record, raw_path, processed_path, count = ingest_open_meteo(
        OpenMeteoConfig("demo_location", 20.5937, 78.9629),
        raw_root=tmp_path / "raw",
        processed_root=tmp_path / "processed",
        fetcher=fake_fetch,
    )

    assert raw_record.source_id == "open_meteo"
    assert raw_path.exists()
    assert processed_path.exists()
    assert count == 10
    assert "/raw/demo_location/2026-10-05/batch.json" in raw_path.as_posix()
    assert "/processed/demo_location/2026-10-05/observations.jsonl" in processed_path.as_posix()
    assert len(processed_path.read_text(encoding="utf-8").splitlines()) == 10
