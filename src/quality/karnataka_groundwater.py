"""Streaming quality profile for Karnataka groundwater candidate records."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any


class KarnatakaGroundwaterProfile:
    """Collect transparent quality diagnostics while CSV rows are streamed."""

    def __init__(self) -> None:
        self.rows_read = 0
        self.accepted_rows = 0
        self.rejected_rows = 0
        self.reject_reasons: Counter[str] = Counter()
        self.stations: set[str] = set()
        self.districts: set[str] = set()
        self.seen_station_times: set[tuple[str, str]] = set()
        self.duplicate_station_timestamps = 0
        self.rows_missing_coordinates = 0
        self.min_timestamp: datetime | None = None
        self.max_timestamp: datetime | None = None
        self.depth_min_m: float | None = None
        self.depth_max_m: float | None = None

    def begin_row(self) -> None:
        self.rows_read += 1

    def reject(self, reason: str) -> None:
        self.rejected_rows += 1
        self.reject_reasons[reason] += 1

    def accept(self, record: dict[str, Any]) -> None:
        key = (str(record["location_id"]), str(record["observed_at"]))
        if key in self.seen_station_times:
            self.duplicate_station_timestamps += 1
            raise ValueError("duplicate station/timestamp observation")
        self.seen_station_times.add(key)
        self.accepted_rows += 1
        self.stations.add(str(record["location_id"]))
        district = record.get("metadata", {}).get("district")
        if district:
            self.districts.add(str(district))
        metadata = record.get("metadata", {})
        if metadata.get("latitude") is None or metadata.get("longitude") is None:
            self.rows_missing_coordinates += 1
        observed = datetime.fromisoformat(
            str(record["observed_at"]).replace("Z", "+00:00")
        )
        self.min_timestamp = (
            observed if self.min_timestamp is None else min(self.min_timestamp, observed)
        )
        self.max_timestamp = (
            observed if self.max_timestamp is None else max(self.max_timestamp, observed)
        )
        depth = float(record["value"])
        self.depth_min_m = depth if self.depth_min_m is None else min(self.depth_min_m, depth)
        self.depth_max_m = depth if self.depth_max_m is None else max(self.depth_max_m, depth)

    def to_dict(self) -> dict[str, Any]:
        accepted = self.accepted_rows
        return {
            "row_counts": {
                "rows_read": self.rows_read,
                "accepted_rows": accepted,
                "rejected_rows": self.rejected_rows,
                "acceptance_rate_pct": round(100.0 * accepted / self.rows_read, 2)
                if self.rows_read else None,
                "reject_reason_counts": dict(sorted(self.reject_reasons.items())),
                "duplicate_station_timestamps": self.duplicate_station_timestamps,
            },
            "coverage": {
                "unique_station_locations": len(self.stations),
                "unique_districts": len(self.districts),
                "start_timestamp": self.min_timestamp.isoformat()
                if self.min_timestamp else None,
                "end_timestamp": self.max_timestamp.isoformat()
                if self.max_timestamp else None,
                "rows_missing_coordinates": self.rows_missing_coordinates,
                "coordinate_completeness_pct": round(
                    100.0 * (accepted - self.rows_missing_coordinates) / accepted, 2
                ) if accepted else None,
            },
            "measurement_range": {
                "min_groundwater_depth_m": self.depth_min_m,
                "max_groundwater_depth_m": self.depth_max_m,
            },
            "review_notes": [
                "Rows are not silently imputed; rejected rows are written to a separate file.",
                "Naive timestamps default to Asia/Kolkata and that assumption must be checked against source documentation.",
                "Station cadence varies; no complete six-hour schedule is assumed and no temporal gaps are auto-corrected.",
                "This is candidate hydrological reference data, not standalone ground truth for the composite surface water-stress index.",
            ],
        }
