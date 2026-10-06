"""Profile a daily AQUA-SENSE JSONL dataset without mutating it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.quality.daily_profile import profile_daily_dataset, quality_flags


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile AQUA-SENSE daily weather quality")
    parser.add_argument("--input", required=True, help="Daily JSONL path")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()

    profile = profile_daily_dataset(read_jsonl(Path(args.input)))
    profile["review_flags"] = quality_flags(profile)
    text = json.dumps(profile, indent=2, sort_keys=True)

    if args.output:
        Path(args.output).write_text(text + "
", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
