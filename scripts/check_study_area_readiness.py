"""Validate a study-area configuration and audit candidate nearby groundwater stations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.alignment.study_area import build_study_area_readiness_report


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number} must contain a JSON object")
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the selected AQUA-SENSE study-area configuration and groundwater station proximity"
    )
    parser.add_argument("--study-area", default="belagavi_city_pilot")
    parser.add_argument("--config", default="config/study_areas.json")
    parser.add_argument("--groundwater-input", help="Optional normalized groundwater JSONL")
    parser.add_argument("--output", default="reports/study_area/belagavi_readiness.json")
    args = parser.parse_args()

    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        study_areas = config["study_areas"]
        if args.study_area not in study_areas:
            raise ValueError(f"unknown study area: {args.study_area}")
        records = read_jsonl(Path(args.groundwater_input)) if args.groundwater_input else []
        report = build_study_area_readiness_report(study_areas[args.study_area], records)
        report["groundwater_records_supplied"] = bool(args.groundwater_input)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "study_area": report["study_area"]["name"],
        "readiness_status": report["readiness_status"],
        "output": str(output_path),
        "automatic_join_performed": report["automatic_join_performed"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
