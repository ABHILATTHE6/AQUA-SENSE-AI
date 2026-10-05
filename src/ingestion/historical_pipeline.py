"""Historical ingestion pipeline for model-training weather data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from src.features.daily_weather import aggregate_daily
from src.ingestion.open_meteo_historical import (
    HistoricalConfig,
    fetch_payload,
    normalize_payload,
    to_raw_record,
)
from src.ingestion.storage import write_raw_json


def ingest_historical_open_meteo(
    config: HistoricalConfig,
    raw_root: str | Path = "data/raw",
    processed_root: str | Path = "data/processed",
    daily_root: str | Path = "data/processed",
    fetcher: Callable[[HistoricalConfig], dict] = fetch_payload,
) -> tuple[Path, Path, Path, int, int]:
    """Fetch, capture raw, normalize, aggregate, and persist historical weather data."""

    payload = fetcher(config)
    raw_record = to_raw_record(config, payload)
    raw_path = write_raw_json(
        raw_root,
        "open_meteo_historical",
        config.start_date,
        [raw_record.as_dict()],
    )

    observations = normalize_payload(config, payload)
    hourly_dir = Path(processed_root) / config.location_id / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    hourly_path = hourly_dir / f"{config.start_date}_{config.end_date}.jsonl"
    hourly_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "
" for item in observations),
        encoding="utf-8",
    )

    daily_rows = aggregate_daily(observations)
    daily_dir = Path(daily_root) / config.location_id / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    daily_path = daily_dir / f"{config.start_date}_{config.end_date}.jsonl"
    daily_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "
" for item in daily_rows),
        encoding="utf-8",
    )

    return raw_path, hourly_path, daily_path, len(observations), len(daily_rows)
