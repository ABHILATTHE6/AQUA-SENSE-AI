import pytest

from src.evaluation.time_split import chronological_split


def rows_for_dates(days=10):
    rows = []
    for day in range(1, days + 1):
        date = f"2026-09-{day:02d}"
        rows.append({"date": date, "location_id": "north", "value": day})
        rows.append({"date": date, "location_id": "south", "value": day + 100})
    return rows


def test_split_is_chronological_and_keeps_same_date_together():
    rows = list(reversed(rows_for_dates()))
    splits = chronological_split(rows)
    assert all(splits[name] for name in ("train", "validation", "test"))
    date_sets = {
        name: {row["date"] for row in split_rows}
        for name, split_rows in splits.items()
    }
    assert date_sets["train"].isdisjoint(date_sets["validation"])
    assert date_sets["train"].isdisjoint(date_sets["test"])
    assert date_sets["validation"].isdisjoint(date_sets["test"])
    assert max(date_sets["train"]) < min(date_sets["validation"])
    assert max(date_sets["validation"]) < min(date_sets["test"])
    for day in {row["date"] for row in rows}:
        assert sum(day in group for group in date_sets.values()) == 1


def test_split_rejects_duplicate_date_entity_pair():
    rows = rows_for_dates(3)
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError, match="duplicate observation"):
        chronological_split(rows)


def test_split_rejects_too_few_unique_dates():
    with pytest.raises(ValueError, match="three unique dates"):
        chronological_split(rows_for_dates(2))


def test_split_validates_fraction_configuration():
    with pytest.raises(ValueError, match="must be below 1"):
        chronological_split(rows_for_dates(), train_fraction=0.8, validation_fraction=0.2)
