"""Leakage-safe lag and rolling features for daily AQUA-SENSE inputs."""

from __future__ import annotations

from datetime import date, timedelta
from statistics import mean
from typing import Any


FEATURE_SPECS = {
    "rainfall_mm_sum": ("sum", (1, 3, 7), (3, 7)),
    "et0_mm_sum": ("sum", (1, 3, 7), (7,)),
    "air_temperature_c_mean": ("mean", (1, 3, 7), (7,)),
    "relative_humidity_pct_mean": ("mean", (1, 7), (7,)),
    "soil_moisture_m3_m3_mean": ("mean", (1, 7), (3,)),
}


def _as_date(value: str) -> date:
    return date.fromisoformat(value)


def _window_values(
    rows_by_date: dict[date, dict[str, Any]],
    current: date,
    field: str,
    window: int,
) -> list[float] | None:
    dates = [current - timedelta(days=offset) for offset in range(1, window + 1)]
    if any(day not in rows_by_date for day in dates):
        return None
    return [float(rows_by_date[day][field]) for day in reversed(dates)]


def add_leakage_safe_features(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add lag and rolling features using only complete prior calendar days.

    Rows are sorted by date. Lag features use exact calendar offsets. Rolling
    features require every day in the prior window to exist; no filling is done.
    """

    if not rows:
        return []

    ordered = sorted((dict(row) for row in rows), key=lambda row: row["date"])
    dates = [_as_date(row["date"]) for row in ordered]
    if len(set(dates)) != len(dates):
        raise ValueError("daily feature engineering requires unique dates")

    by_date = {date_value: row for date_value, row in zip(dates, ordered)}
    output: list[dict[str, Any]] = []

    for row, current in zip(ordered, dates):
        enriched = dict(row)

        for field, (_, lags, windows) in FEATURE_SPECS.items():
            for lag in lags:
                source = by_date.get(current - timedelta(days=lag))
                enriched[f"{field}_lag_{lag}d"] = (
                    None if source is None else source.get(field)
                )

            for window in windows:
                values = _window_values(by_date, current, field, window)
                enriched[f"{field}_rolling_{window}d"] = (
                    None if values is None else round(mean(values), 6)
                )

            # Flux variables need cumulative history, while state variables use means.
            if field in {"rainfall_mm_sum", "et0_mm_sum"}:
                for window in windows:
                    values = _window_values(by_date, current, field, window)
                    enriched[f"{field}_rolling_sum_{window}d"] = (
                        None if values is None else round(sum(values), 6)
                    )

        output.append(enriched)

    return output
