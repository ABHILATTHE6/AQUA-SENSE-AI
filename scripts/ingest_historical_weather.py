"""CLI for bounded historical weather ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ingestion.historical_pipeline import ingest_historical_open_meteo
from src.ingestion.open_meteo_historical import HistoricalConfig


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest historical Open-Meteo weather for AQUA-SENSE AI"
    )
    parser.add_argument("--location", default="demo_location")
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--model", default="era5")
    parser.add_argument("--config", default="config/locations.json")
    args = parser.parse_args()

    locations = json.loads(Path(args.config).read_text(encoding="utf-8"))
    location = locations[args.location]
    config = HistoricalConfig(
        location_id=args.location,
        latitude=float(location["latitude"]),
        longitude=float(location["longitude"]),
        start_date=args.start_date,
        end_date=args.end_date,
        model=args.model,
    )
    raw, hourly, daily, hourly_count, daily_count = ingest_historical_open_meteo(config)
    print(f"Ingested {hourly_count} hourly observations")
    print(f"Complete daily rows: {daily_count}")
    print(f"Raw: {raw}")
    print(f"Hourly: {hourly}")
    print(f"Daily: {daily}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
