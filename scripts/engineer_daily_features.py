"""Build leakage-safe daily feature JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.features.lagged import add_leakage_safe_features


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Engineer leakage-safe AQUA-SENSE features")
    parser.add_argument("--input", required=True, help="Daily JSONL input")
    parser.add_argument("--output", required=True, help="Feature JSONL output")
    args = parser.parse_args()

    rows = add_leakage_safe_features(read_jsonl(Path(args.input)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "
" for row in rows),
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} feature rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
