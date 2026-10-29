import pytest

from src.evaluation.time_split import chronological_split


def daily_rows(days=10):
    rows = []
    for day in range(1, days + 1):
        date = f"2026-09-{day:02d}"
        rows.extend([
            {"date": date, "location_id": "north", "value": day},
            {"date": date, "location_id": "south", "value": day + 100},
        ])
    return rows


def test_split_is_ordered_and_keeps_same_date_together():
    splits = chronological_split(list(reversed(daily_rows())))
    date_sets = {name: {row["date"] for row in values} for name, values in splits.items()}
    assert all(splits[name] for name in ("train", "validation", "test"))
    assert date_sets["train"].isdisjoint(date_sets["validation"])
    assert date_sets["train"].isdisjoint(date_sets["test"])
    assert date_sets["validation"].isdisjoint(date_sets["test"])
    assert max(date_sets["train"]) < min(date_sets["validation"])
    assert max(date_sets["validation"]) < min(date_sets["test"])
    for day in {row["date"] for row in daily_rows()}:
        assert sum(day in values for values in date_sets.values()) == 1


def test_split_rejects_duplicate_date_entity():
    rows = daily_rows(3)
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError, match="duplicate observation"):
        chronological_split(rows)


def test_split_rejects_less_than_three_dates():
    with pytest.raises(ValueError, match="three unique dates"):
        chronological_split(daily_rows(2))


def test_split_validates_fractions():
    with pytest.raises(ValueError, match="must be below 1"):
        chronological_split(daily_rows(), train_fraction=0.8, validation_fraction=0.2)
