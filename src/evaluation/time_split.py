"""Chronological dataset partitioning with date-level leakage safeguards."""

from __future__ import annotations

from datetime import date
from typing import Any


def _parse_date(row: dict[str, Any], date_field: str, row_number: int) -> date:
    value = row.get(date_field)
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError(f"row {row_number} must contain an ISO date in '{date_field}'")
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError(
            f"row {row_number} has an invalid ISO date in '{date_field}': {value!r}"
        ) from exc


def chronological_split(
    rows: list[dict[str, Any]],
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
    date_field: str = "date",
    entity_field: str = "location_id",
) -> dict[str, list[dict[str, Any]]]:
    """Split observations chronologically, keeping each date in one partition.

    All locations recorded on the same calendar date stay together. No random
    shuffling occurs. Duplicate date/entity keys are rejected. This is a
    protocol utility for future predictive work; it does not validate today's
    deterministic rule-based index.
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
    seen_keys: set[tuple[date, Any]] = set()
    for index, original in enumerate(rows, start=1):
        row = dict(original)
        day = _parse_date(row, date_field, index)
        entity = row.get(entity_field)
        try:
            key = (day, entity)
            duplicate = key in seen_keys
            seen_keys.add(key)
        except TypeError as exc:
            raise ValueError(
                f"row {index} has a non-scalar '{entity_field}' identity"
            ) from exc
        if duplicate:
            raise ValueError(
                f"duplicate observation for {entity_field}={entity!r} on {day.isoformat()}"
            )
        prepared.append((day, row))

    unique_days = sorted({day for day, _ in prepared})
    if len(unique_days) < 3:
        raise ValueError("at least three unique dates are required for train/validation/test splits")

    n_days = len(unique_days)
    train_end = max(1, min(n_days - 2, int(n_days * train_fraction)))
    validation_end = max(
        train_end + 1,
        min(n_days - 1, int(n_days * (train_fraction + validation_fraction))),
    )
    train_days = set(unique_days[:train_end])
    validation_days = set(unique_days[train_end:validation_end])
    test_days = set(unique_days[validation_end:])
    day_to_partition = {
        **{day: "train" for day in train_days},
        **{day: "validation" for day in validation_days},
        **{day: "test" for day in test_days},
    }

    result: dict[str, list[dict[str, Any]]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    for day, row in sorted(
        prepared, key=lambda item: (item[0], str(item[1].get(entity_field, "")))
    ):
        result[day_to_partition[day]].append(row)
    return result
