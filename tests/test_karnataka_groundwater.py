import csv
import json
from pathlib import Path

import pytest

from src.ingestion.karnataka_groundwater import (
    DEFAULT_SOURCE_TIMEZONE,
    normalize_groundwater_row,
    resolve_columns,
)
from src.quality.karnataka_groundwater import KarnatakaGroundwaterProfile
from src.validation.reference_target import validate_reference_target
from scripts.ingest_karnataka_groundwater import process_csv

FIXTURE = Path(__file__).parent / "fixtures" / "karnataka_groundwater_sample.csv"


def load_fixture_rows():
    with FIXTURE.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return reader.fieldnames, rows


def test_resolves_portal_header_and_normalizes_candidate_record():
    headers, rows = load_fixture_rows()
    record = normalize_groundwater_row(rows[0], row_number=1, fieldnames=headers)
    validate_reference_target(record)
    assert record["source"] == "karnataka_groundwater"
    assert record["target_variable"] == "groundwater_depth_m"
    assert record["value"] == 8.25
    assert record["unit"] == "m"
    assert record["observed_at"] == "2025-01-01T06:00:00+05:30"
    assert record["independence_assessment"]["status"] == "candidate"
    assert record["metadata"]["latitude"] == 12.3
    assert DEFAULT_SOURCE_TIMEZONE == "Asia/Kolkata"


def test_preserves_explicit_timestamp_offset():
    headers, rows = load_fixture_rows()
    rows[0]["Data Acquisition Time"] = "2025-01-01T00:30:00Z"
    record = normalize_groundwater_row(rows[0], row_number=1, fieldnames=headers)
    assert record["observed_at"] == "2025-01-01T00:30:00+00:00"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("Groundwater Level Telemetry 6 Hourly (meter)", "-1.0", "non-negative"),
        ("Groundwater Level Telemetry 6 Hourly (meter)", "not-a-number", "not numeric"),
        ("Data Acquisition Time", "", "missing observation timestamp"),
        ("Station", "", "missing station"),
    ],
)
def test_rejects_invalid_rows(field, value, message):
    headers, rows = load_fixture_rows()
    row = dict(rows[0])
    row[field] = value
    with pytest.raises(ValueError, match=message):
        normalize_groundwater_row(row, row_number=1, fieldnames=headers)


def test_rejects_unknown_required_header():
    with pytest.raises(ValueError, match="required CSV column not found"):
        resolve_columns(["Timestamp", "Station", "unrelated column"])


def test_profile_reports_coverage_and_reject_reasons():
    headers, rows = load_fixture_rows()
    profile = KarnatakaGroundwaterProfile()
    profile.begin_row()
    profile.accept(normalize_groundwater_row(rows[0], row_number=1, fieldnames=headers))
    profile.begin_row()
    profile.reject("invalid test row")
    report = profile.to_dict()
    assert report["row_counts"]["rows_read"] == 2
    assert report["row_counts"]["accepted_rows"] == 1
    assert report["row_counts"]["rejected_rows"] == 1
    assert report["coverage"]["unique_station_locations"] == 1
    assert report["measurement_range"]["min_groundwater_depth_m"] == 8.25


def test_cli_processing_writes_normalized_jsonl(tmp_path):
    output = tmp_path / "normalized" / "records.jsonl"
    rejects = tmp_path / "rejected" / "records.jsonl"
    profile = process_csv(FIXTURE, output, rejects, limit=2)
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert profile["row_counts"]["accepted_rows"] == 2
    assert profile["row_counts"]["rejected_rows"] == 0
    assert rejects.read_text(encoding="utf-8") == ""
