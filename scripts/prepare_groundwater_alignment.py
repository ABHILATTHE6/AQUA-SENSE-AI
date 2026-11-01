"""Create local-day groundwater summaries and a spatial match audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.features.groundwater_alignment import (
    aggregate_groundwater_daily,
    build_station_weather_candidates,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number} must contain a JSON object")
        rows.append(value)
    return rows


def read_weather_locations(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "locations" in payload:
        payload = payload["locations"]
    if isinstance(payload, dict):
        return [
            {
                "location_id": location_id,
                "latitude": values.get("latitude"),
                "longitude": values.get("longitude"),
            }
            for location_id, values in payload.items()
            if isinstance(values, dict)
        ]
    if isinstance(payload, list):
        return payload
    raise ValueError("weather locations JSON must be an object or a list")


def run_alignment_preparation(
    records: list[dict[str, Any]],
    weather_locations: list[dict[str, Any]],
    *,
    timezone_name: str = "Asia/Kolkata",
    expected_observations_per_day: int = 4,
    minimum_observations: int = 3,
    maximum_distance_km: float = 10.0,
    ambiguity_margin_km: float = 1.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    daily = aggregate_groundwater_daily(
        records,
        timezone_name=timezone_name,
        expected_observations_per_day=expected_observations_per_day,
        minimum_observations=minimum_observations,
    )
    candidates = build_station_weather_candidates(
        records,
        weather_locations,
        maximum_distance_km=maximum_distance_km,
        ambiguity_margin_km=ambiguity_margin_km,
    )
    daily_counts = Counter(row["daily_summary_status"] for row in daily)
    match_counts = Counter(row["match_status"] for row in candidates)
    report = {
        "report_version": "1.0",
        "timezone": timezone_name,
        "daily_summary": {
            "summary_rows": len(daily),
            "station_count": len({row["location_id"] for row in daily}),
            "local_date_count": len({row["date"] for row in daily}),
            "sufficient_observation_days": daily_counts.get("sufficient_observations", 0),
            "insufficient_observation_days": daily_counts.get("insufficient_observations", 0),
            "expected_observations_per_day": expected_observations_per_day,
            "minimum_observations_required": minimum_observations,
        },
        "spatial_candidate_matching": {
            "station_count": len(candidates),
            "weather_location_count": len(weather_locations),
            "status_counts": dict(sorted(match_counts.items())),
            "candidates": candidates,
            "maximum_distance_km": maximum_distance_km,
            "ambiguity_margin_km": ambiguity_margin_km,
            "automatic_join_performed": False,
        },
        "temporal_join_policy": (
            "Aggregate station and weather hourly observations in the same named "
            "timezone before comparing local calendar dates. UTC daily weather "
            "aggregates must not be joined directly to Asia/Kolkata groundwater days."
        ),
        "ground_truth_status": "candidate_not_approved",
        "predictive_accuracy_assessed": False,
        "interpretation": (
            "This report audits daily coverage and nearby weather-location candidates. "
            "It does not merge observations or establish target validity."
        ),
    }
    return daily, report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize groundwater readings by local day and audit nearby weather points"
    )
    parser.add_argument("--input", required=True, help="Normalized groundwater reference JSONL")
    parser.add_argument("--weather-locations", default="config/locations.json")
    parser.add_argument(
        "--daily-output",
        default="data/processed/reference/karnataka_groundwater_daily.jsonl",
    )
    parser.add_argument(
        "--report",
        default="reports/alignment/karnataka_groundwater_weather_candidates.json",
    )
    parser.add_argument("--timezone", default="Asia/Kolkata")
    parser.add_argument("--expected-observations-per-day", type=int, default=4)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--maximum-distance-km", type=float, default=10.0)
    parser.add_argument("--ambiguity-margin-km", type=float, default=1.0)
    args = parser.parse_args()

    try:
        records = read_jsonl(Path(args.input))
        weather = read_weather_locations(Path(args.weather_locations))
        daily, report = run_alignment_preparation(
            records,
            weather,
            timezone_name=args.timezone,
            expected_observations_per_day=args.expected_observations_per_day,
            minimum_observations=args.minimum_observations,
            maximum_distance_km=args.maximum_distance_km,
            ambiguity_margin_km=args.ambiguity_margin_km,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    daily_path, report_path = Path(args.daily_output), Path(args.report)
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    daily_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in daily),
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(daily)} station-day summaries and "
        f"{report['spatial_candidate_matching']['station_count']} spatial match audits."
    )
    print("No weather join was performed; candidate references remain unapproved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
