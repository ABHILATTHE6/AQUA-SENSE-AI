from datetime import datetime, timezone
from pathlib import Path

from src.ingestion.base import RawRecord, utc_now
from src.ingestion.storage import raw_partition, write_raw_json

def test_raw_record_preserves_provider_payload():
    record = RawRecord(
        source_id='test-source',
        retrieved_at=datetime(2026, 9, 30, tzinfo=timezone.utc),
        payload={'provider_field': 12.5},
        source_location='LOC001',
    )
    result = record.as_dict()
    assert result['source_id'] == 'test-source'
    assert result['payload'] == {'provider_field': 12.5}

def test_raw_partition_is_deterministic():
    assert raw_partition('data/raw', 'open_meteo', '2026-09-30') == Path('data/raw/open_meteo/2026-09-30')

def test_write_raw_json_creates_partition(tmp_path):
    output = write_raw_json(tmp_path, 'test-source', '2026-09-30', [{'value': 1}])
    assert output.exists()
    assert output.read_text(encoding='utf-8').strip().startswith('[')

def test_utc_now_is_timezone_aware():
    assert utc_now().tzinfo is not None
