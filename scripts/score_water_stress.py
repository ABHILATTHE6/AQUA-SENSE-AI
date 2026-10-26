"""Compute the transparent AQUA-SENSE rule-based water-stress index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.scoring.water_stress import score_dataset


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Score daily water stress using baseline v1")
    parser.add_argument("--input", required=True, help="Daily JSONL dataset")
    parser.add_argument("--output", required=True, help="Output scores JSONL")
    args = parser.parse_args()

    scores = score_dataset(read_jsonl(Path(args.input)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in scores),
        encoding="utf-8",
    )
    print(f"Wrote {len(scores)} water-stress scores to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main)
