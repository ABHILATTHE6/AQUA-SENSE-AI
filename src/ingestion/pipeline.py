"""Reusable ingestion pipeline helpers for external weather sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from src.ingestion.base import RawRecord
from src.ingestion.open_meteo import OpenMeteoConfig, fetch_payload, normalize_payload, to_raw_record
from src.ingestion.storage import write_raw_json


def ingest_open_meteo(
    config: OpenMeteoConfig,
    raw_root: str | Path = "data/raw",
    processed_root: str | Path = "data/processed",
    fetcher: Callable[[OpenMeteoConfig], dict] = fetch_payload,
) -> tuple[RawRecord, Path, Path, int]:
    """Fetch, capture raw, normalize, validate, and persist one Open-Meteo batch."""

    payload = fetcher(config)
    raw_record = to_raw_record(config, payload)
    observed_date = str(payload["hourly"]["time"][0])[:10]
    raw_path = write_raw_json(raw_root, config.location_id, observed_date, [raw_record.as_dict()])

    observations = normalize_payload(config, payload)
    processed_dir = Path(processed_root) / config.location_id / observed_date
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path = processed_dir / "observations.jsonl"
    processed_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "
" for item in observations),
        encoding="utf-8",
    )
    return raw_record, raw_path, processed_path, len(observations)
