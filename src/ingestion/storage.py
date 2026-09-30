"""Filesystem conventions for immutable raw ingestion artifacts."""

from pathlib import Path
from typing import Any
import json

def raw_partition(root: str | Path, source_id: str, observed_date: str) -> Path:
    """Return the deterministic raw partition path for a source/date."""
    return Path(root) / source_id / observed_date

def write_raw_json(root: str | Path, source_id: str, observed_date: str, records: list[dict[str, Any]]) -> Path:
    """Write a raw batch as JSON without transforming provider fields."""
    directory = raw_partition(root, source_id, observed_date)
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / 'batch.json'
    output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return output
