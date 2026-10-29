"""Chronological partitions with date-level leakage safeguards."""

from __future__ import annotations

from datetime import date
from typing import Any


def _parse_date(row: dict[str, Any], date_field: str, row_number: int) -> date:
    value = row.get(date_field)
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError(f"row {row_number} must contain an ISO date in {date_field!r}")
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError(f"row {row_number} has an invalid ISO date: {value!r}") from exc


def chronological_split(
    rows: list[dict[str, Any]],
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
    date_field: str = "date",
    entity_field: str = "location_id",
) -> dict[str, list[dict[str, Any]]]:
    """Split rows by unique calendar dates, without random shuffling.

    Every location on a given date goes into the same partition. Duplicate
    (date, entity) keys are rejected so duplicates cannot silently bias results.
    This helper is designed for future predictive evaluation; its use does not
    indicate that the current rule-based index has been validated.
    """
    if not rows:
        raise ValueError("cannot split an empty dataset")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train_fraction + validation_fraction must be below 1")

    prepared: list[tuple[date, dict[str, Any]]] = []
    seen: set[tuple[date, Any]] = set()
    for index, original in enumerate(rows, start=1):
        row = dict(original)
        day = _parse_date(row, date_field, index)
        entity = row.get(entity_field)
        try:
            key = (day, entity)
            is_duplicate = key in seen
            seen.add(key)
        except TypeError as exc:
            raise ValueError(f"row {index} has a non-scalar entity identifier") from exc
        if is_duplicate:
            raise ValueError(
                f"duplicate observation for {entity_field}={entity!r} on {day.isoformat()}"
            )
        prepared.append((day, row))

    days = sorted({day for day, _ in prepared})
    if len(days) < 3:
        raise ValueError("at least three unique dates are required for train/validation/test splits")

    count = len(days)
    train_end = max(1, min(count - 2, int(count * train_fraction)))
    validation_end = max(
        train_end + 1,
        min(count - 1, int(count * (train_fraction + validation_fraction))),
    )
    groups: dict[str, set[date]] = {
        "train": set(days[:train_end]),
        "validation": set(days[train_end:validation_end]),
        "test": set(days[validation_end:]),
    }
    assignment = {day: name for name, group in groups.items() for day in group}
    result: dict[str, list[dict[str, Any]]] = {
        "train": [], "validation": [], "test": []
    }
    for day, row in sorted(prepared, key=lambda item: (item[0], str(item[1].get(entity_field, "")))):
        result[assignment[day]].append(row)
    return result
