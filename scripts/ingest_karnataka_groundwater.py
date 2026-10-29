"""Download and profile Karnataka groundwater telemetry as candidate reference data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ingestion.karnataka_groundwater import (
    DEFAULT_SOURCE_TIMEZONE,
    SOURCE_DATASET_URL,
    SOURCE_DOWNLOAD_URL,
    normalize_groundwater_row,
    resolve_columns,
)
from src.quality.karnataka_groundwater import KarnatakaGroundwaterProfile
from src.validation.reference_target import validate_reference_target

USER_AGENT = "AQUA-SENSE-AI/0.1 (public-data ingestion; timeout and size guard enabled)"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_csv(url: str, destination: Path, *, max_bytes: int) -> dict[str, Any]:
    """Stream a CSV to the raw layer with a byte cap and atomic finalization."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    written = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise ValueError(
                    f"source declares {content_length} bytes, above the configured "
                    f"{max_bytes}-byte cap"
                )
            with temporary.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        raise ValueError(f"download exceeded configured {max_bytes}-byte cap")
                    digest.update(chunk)
                    output.write(chunk)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "url": url,
        "bytes": written,
        "sha256": digest.hexdigest(),
        "content_sha256_algorithm": "sha256",
    }


def _raw_row_for_json(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in row.items() if key is not None}


def process_csv(
    csv_path: Path,
    output_path: Path,
    rejects_path: Path,
    *,
    source_timezone: str = DEFAULT_SOURCE_TIMEZONE,
    source_url: str = SOURCE_DOWNLOAD_URL,
    limit: int | None = None,
) -> dict[str, Any]:
    """Normalize valid rows, quarantine invalid rows, and return a quality report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rejects_path.parent.mkdir(parents=True, exist_ok=True)
    profile = KarnatakaGroundwaterProfile()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("source CSV has no header row")
        columns = resolve_columns(reader.fieldnames)
        with output_path.open("w", encoding="utf-8", newline="\n") as output:
            with rejects_path.open("w", encoding="utf-8", newline="\n") as rejects:
                for row_number, raw_row in enumerate(reader, start=1):
                    if limit is not None and row_number > limit:
                        break
                    profile.begin_row()
                    clean_raw = _raw_row_for_json(raw_row)
                    try:
                        record = normalize_groundwater_row(
                            clean_raw,
                            row_number=row_number,
                            fieldnames=reader.fieldnames,
                            source_timezone=source_timezone,
                            source_url=source_url,
                            column_mapping=columns,
                        )
                        validate_reference_target(record)
                        profile.accept(record)
                        output.write(
                            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                        )
                    except (TypeError, ValueError) as exc:
                        reason = str(exc)
                        profile.reject(reason)
                        rejects.write(json.dumps({
                            "source_row_number": row_number,
                            "reason": reason,
                            "raw_row": clean_raw,
                        }, ensure_ascii=False, sort_keys=True) + "\n")
    return profile.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and normalize Karnataka groundwater telemetry as candidate reference data"
    )
    parser.add_argument("--input", help="Use an existing local provider CSV; skips network download")
    parser.add_argument("--url", default=SOURCE_DOWNLOAD_URL, help="Provider CSV download URL")
    parser.add_argument("--raw-output", help="Raw CSV destination; defaults to a dated data/raw partition")
    parser.add_argument("--output", default="data/processed/reference/karnataka_groundwater.jsonl")
    parser.add_argument("--rejects", default="data/processed/rejected/karnataka_groundwater.jsonl")
    parser.add_argument("--report", default="reports/data_quality/karnataka_groundwater.json")
    parser.add_argument("--source-timezone", default=DEFAULT_SOURCE_TIMEZONE,
                        help="Timezone assumed for timestamps without an offset")
    parser.add_argument("--limit", type=int, help="Process only the first N data rows after download")
    parser.add_argument("--max-download-mib", type=float, default=2048.0,
                        help="Maximum download size in MiB; defaults to 2048 MiB")
    parser.add_argument("--force-download", action="store_true",
                        help="Download even if the raw destination already exists")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.max_download_mib <= 0:
        parser.error("--max-download-mib must be positive")

    acquired_at = datetime.now(timezone.utc).isoformat()
    if args.input:
        csv_path = Path(args.input)
        if not csv_path.is_file():
            parser.error(f"input CSV does not exist: {csv_path}")
        download_info = {
            "downloaded_in_this_run": False,
            "provided_local_path": str(csv_path),
            "bytes": csv_path.stat().st_size,
            "sha256": sha256_file(csv_path),
            "url": args.url,
        }
    else:
        raw_path = Path(args.raw_output) if args.raw_output else Path(
            "data/raw/karnataka_groundwater/"
            + datetime.now(timezone.utc).date().isoformat()
            + "/karnataka_gwl_2021_2025.csv"
        )
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if raw_path.exists() and not args.force_download:
            csv_path = raw_path
            download_info = {
                "downloaded_in_this_run": False,
                "reused_existing_raw_file": True,
                "bytes": csv_path.stat().st_size,
                "sha256": sha256_file(csv_path),
                "url": args.url,
            }
        else:
            csv_path = raw_path
            try:
                download_info = {
                    "downloaded_in_this_run": True,
                    **download_csv(
                        args.url,
                        csv_path,
                        max_bytes=int(args.max_download_mib * 1024 * 1024),
                    ),
                }
            except Exception as exc:
                parser.error(
                    f"download failed: {exc}. Use --input with a locally downloaded CSV to process offline."
                )

    output_path, rejects_path, report_path = (
        Path(args.output), Path(args.rejects), Path(args.report)
    )
    try:
        profile = process_csv(
            csv_path,
            output_path,
            rejects_path,
            source_timezone=args.source_timezone,
            source_url=args.url,
            limit=args.limit,
        )
    except (OSError, ValueError) as exc:
        parser.error(f"could not profile CSV: {exc}")

    report = {
        "report_version": "1.0",
        "source_id": "karnataka_groundwater",
        "dataset_url": SOURCE_DATASET_URL,
        "acquired_at_utc": acquired_at,
        "source_timezone_assumption": args.source_timezone,
        "download": download_info,
        "raw_csv_path": str(csv_path),
        "normalized_jsonl_path": str(output_path),
        "rejected_rows_jsonl_path": str(rejects_path),
        "row_limit_applied": args.limit,
        "profile": profile,
        "ground_truth_status": "candidate_not_approved",
        "predictive_accuracy_assessed": False,
        "interpretation": (
            "This acquisition and quality report describes groundwater telemetry only. "
            "It does not validate the composite surface water-stress index."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    counts = profile["row_counts"]
    print(
        f"Read {counts['rows_read']} rows: {counts['accepted_rows']} accepted, "
        f"{counts['rejected_rows']} rejected. Report: {report_path}"
    )
    print("Records remain candidate reference data; the script does not approve ground truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
