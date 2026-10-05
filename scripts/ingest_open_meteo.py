"""CLI entry point for a real Open-Meteo forecast ingestion run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ingestion.open_meteo import OpenMeteoConfig
from src.ingestion.pipeline import ingest_open_meteo


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest an Open-Meteo forecast into AQUA-SENSE layers")
    parser.add_argument("--location", default="demo_location", help="Location ID from config/locations.json")
    parser.add_argument("--forecast-days", type=int, default=3, choices=range(1, 17))
    parser.add_argument("--config", default="config/locations.json")
    args = parser.parse_args()

    locations = json.loads(Path(args.config).read_text(encoding="utf-8"))
    location = locations[args.location]
    config = OpenMeteoConfig(
        location_id=args.location,
        latitude=float(location["latitude"]),
        longitude=float(location["longitude"]),
        forecast_days=args.forecast_days,
    )
    _, raw_path, processed_path, count = ingest_open_meteo(config)
    print(f"Ingested {count} observations from {config.location_id}")
    print(f"Raw: {raw_path}")
    print(f"Processed: {processed_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
