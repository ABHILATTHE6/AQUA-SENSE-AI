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
    parser.add_argument("--model", help="Open-Meteo reanalysis model; defaults to location config or era5")
    parser.add_argument("--timezone", help="IANA timezone; defaults to location config or UTC")
    parser.add_argument("--config", default="config/locations.json")
    args = parser.parse_args()

    locations = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.location not in locations:
        parser.error(f"unknown location_id: {args.location}")
    location = locations[args.location]
    config = HistoricalConfig(
        location_id=args.location,
        latitude=float(location["latitude"]),
        longitude=float(location["longitude"]),
        start_date=args.start_date,
        end_date=args.end_date,
        timezone=args.timezone or location.get("timezone", "UTC"),
        model=args.model or location.get("model", "era5"),
    )
    try:
        config.validate()
        raw, hourly, daily, hourly_count, daily_count = ingest_historical_open_meteo(config)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(f"Ingested {hourly_count} hourly observations for {config.location_id}")
    print(f"Complete daily rows: {daily_count}")
    print(f"Timezone: {config.timezone}; model: {config.model}")
    print(f"Raw: {raw}")
    print(f"Hourly: {hourly}")
    print(f"Daily: {daily}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
