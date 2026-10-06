"""Data-quality profiling for AQUA-SENSE daily training inputs."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from math import isnan
from statistics import mean


NUMERIC_FIELDS = (
    "rainfall_mm_sum",
    "air_temperature_c_mean",
    "relative_humidity_pct_mean",
    "et0_mm_sum",
    "soil_moisture_m3_m3_mean",
)


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("cannot calculate a percentile from empty values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _numeric_summary(values: list[float]) -> dict[str, float | int]:
    clean = [value for value in values if not isnan(value)]
    if not clean:
        return {"count": 0, "missing": len(values)}
    q1 = _percentile(clean, 0.25)
    q3 = _percentile(clean, 0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = sum(value < lower or value > upper for value in clean)
    return {
        "count": len(clean),
        "missing": len(values) - len(clean),
        "min": min(clean),
        "max": max(clean),
        "mean": mean(clean),
        "p25": q1,
        "median": _percentile(clean, 0.50),
        "p75": q3,
        "iqr": iqr,
        "outlier_count_iqr": outliers,
    }


def _missing_date_count(rows: list[dict]) -> int:
    dates = sorted(date.fromisoformat(row["date"]) for row in rows)
    if len(dates) < 2:
        return 0
    return sum(
        max((right - left).days - 1, 0)
        for left, right in zip(dates, dates[1:])
    )


def profile_daily_dataset(rows: list[dict]) -> dict:
    """Return quality metrics without mutating or imputing the dataset."""

    if not rows:
        return {
            "row_count": 0,
            "duplicate_date_count": 0,
            "missing_calendar_day_count": 0,
            "numeric": {},
        }

    dates = [row["date"] for row in rows]
    counts = Counter(dates)
    numeric: dict[str, dict] = {}

    for field in NUMERIC_FIELDS:
        values = []
        missing = 0
        for row in rows:
            value = row.get(field)
            if value is None:
                missing += 1
            else:
                values.append(float(value))
        summary = _numeric_summary(values + [float("nan")] * missing)
        numeric[field] = summary

    return {
        "row_count": len(rows),
        "location_ids": sorted({row.get("location_id") for row in rows}),
        "start_date": min(dates),
        "end_date": max(dates),
        "unique_date_count": len(counts),
        "duplicate_date_count": sum(max(count - 1, 0) for count in counts.values()),
        "missing_calendar_day_count": _missing_date_count(rows),
        "complete_hourly_day_count": sum(
            row.get("complete_hourly_day") is True for row in rows
        ),
        "numeric": numeric,
    }


def quality_flags(profile: dict) -> list[str]:
    """Convert profile findings into review flags; never auto-correct data."""

    flags: list[str] = []
    if profile.get("duplicate_date_count", 0):
        flags.append("duplicate_dates")
    if profile.get("missing_calendar_day_count", 0):
        flags.append("calendar_gaps")
    if any(
        summary.get("missing", 0)
        for summary in profile.get("numeric", {}).values()
    ):
        flags.append("missing_values")
    if any(
        summary.get("outlier_count_iqr", 0)
        for summary in profile.get("numeric", {}).values()
    ):
        flags.append("iqr_outliers")
    return flags
