"""Create a sensitivity report for the rule-based water-stress baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.sensitivity import build_sensitivity_report


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number} must be a JSON object")
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare rule-based water-stress configurations without accuracy claims"
    )
    parser.add_argument("--input", required=True, help="Daily weather JSONL input")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    args = parser.parse_args()
    try:
        report = build_sensitivity_report(read_jsonl(Path(args.input)))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote sensitivity report for {report['dataset_window']['row_count']} rows "
        f"to {output}. Predictive accuracy was not assessed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
