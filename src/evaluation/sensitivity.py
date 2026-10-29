"""Descriptive sensitivity analysis for the exploratory water-stress index.

The module deliberately does not report predictive accuracy: an independent
reference target is not yet integrated into this project's baseline workflow.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from statistics import mean, median
from typing import Any

from src.evaluation.time_split import chronological_split
from src.scoring.water_stress import StressConfig, score_dataset

CATEGORIES = ("low", "moderate", "high", "very_high")


def scenario_configs() -> list[tuple[str, str, StressConfig]]:
    """Return the documented, deterministic configurations used in the report."""
    default = StressConfig()
    return [
        ("baseline_v1", "Current documented defaults.", default),
        ("equal_weights", "Equal weight for all four components.", replace(
            default, rainfall_weight=0.25, soil_moisture_weight=0.25,
            et0_weight=0.25, heat_weight=0.25)),
        ("soil_moisture_emphasis", "Higher soil-moisture weight.", replace(
            default, rainfall_weight=0.15, soil_moisture_weight=0.50,
            et0_weight=0.20, heat_weight=0.15)),
        ("atmospheric_demand_emphasis", "Higher combined ET0 and heat weights.", replace(
            default, rainfall_weight=0.20, soil_moisture_weight=0.25,
            et0_weight=0.35, heat_weight=0.20)),
        ("tighter_upper_thresholds", "Alternative upper normalization thresholds.", replace(
            default, rainfall_wet_mm=15.0, soil_moisture_wet=0.35,
            et0_high_mm=7.0, temperature_high_c=38.0)),
    ]


def summarize_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    if not scores:
        return {
            "count": 0, "mean_score": None, "median_score": None,
            "min_score": None, "max_score": None,
            "category_counts": {name: 0 for name in CATEGORIES},
        }
    values = [float(row["water_stress_index"]) for row in scores]
    counts = Counter(row["water_stress_category"] for row in scores)
    return {
        "count": len(scores),
        "mean_score": round(mean(values), 3),
        "median_score": round(median(values), 3),
        "min_score": round(min(values), 3),
        "max_score": round(max(values), 3),
        "category_counts": {name: counts.get(name, 0) for name in CATEGORIES},
    }


def compare_scores(
    baseline_scores: list[dict[str, Any]], comparison_scores: list[dict[str, Any]]
) -> dict[str, Any]:
    """Quantify score shifts and category changes for aligned observations."""
    if not baseline_scores:
        raise ValueError("cannot compare empty score collections")
    if len(baseline_scores) != len(comparison_scores):
        raise ValueError("score collections must have equal length")

    def keyed(rows: list[dict[str, Any]]) -> dict[tuple[Any, Any], dict[str, Any]]:
        result = {}
        for row in rows:
            key = (row.get("date"), row.get("location_id"))
            if key in result:
                raise ValueError("duplicate date/location key in score collection")
            result[key] = row
        return result

    baseline = keyed(baseline_scores)
    compared = keyed(comparison_scores)
    if baseline.keys() != compared.keys():
        raise ValueError("score collections must cover the same date/location observations")
    shifts = [abs(float(compared[k]["water_stress_index"]) - float(v["water_stress_index"]))
              for k, v in baseline.items()]
    changes = sum(
        compared[k]["water_stress_category"] != v["water_stress_category"]
        for k, v in baseline.items()
    )
    return {
        "mean_absolute_score_shift": round(mean(shifts), 3),
        "max_absolute_score_shift": round(max(shifts), 3),
        "category_changes": changes,
        "category_change_rate_pct": round(100.0 * changes / len(baseline), 2),
    }


def _window(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = sorted(str(row["date"])[:10] for row in rows)
    return {
        "start_date": values[0] if values else None,
        "end_date": values[-1] if values else None,
        "unique_dates": len(set(values)),
        "row_count": len(rows),
    }


def build_sensitivity_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Score one dataset across alternatives; no ground-truth accuracy is inferred."""
    if not rows:
        raise ValueError("input dataset has no daily records")

    # Ensure observations are uniquely identifiable before running comparisons.
    keys = [(str(row.get("date", ""))[:10], row.get("location_id")) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("input contains duplicate date/location observations")

    configs = scenario_configs()
    score_sets = [(name, description, config, score_dataset(rows, config))
                  for name, description, config in configs]
    baseline = score_sets[0][3]
    scenario_results = []
    for name, description, config, scores in score_sets:
        scenario_results.append({
            "scenario_id": name,
            "description": description,
            "configuration": asdict(config),
            "summary": summarize_scores(scores),
            "comparison_to_baseline": compare_scores(baseline, scores),
        })

    temporal: dict[str, Any]
    try:
        splits = chronological_split(rows)
        period_results = {}
        for period_name, period_rows in splits.items():
            period_baseline = score_dataset(period_rows)
            period_scenarios = {}
            for name, description, config in configs:
                scores = score_dataset(period_rows, config)
                period_scenarios[name] = {
                    "summary": summarize_scores(scores),
                    "comparison_to_baseline": compare_scores(period_baseline, scores),
                }
            period_results[period_name] = {
                "window": _window(period_rows),
                "baseline_summary": summarize_scores(period_baseline),
                "scenarios": period_scenarios,
            }
        temporal = {
            "available": True,
            "purpose": "Descriptive comparisons by chronological period, not model evaluation.",
            "partitions": period_results,
        }
    except ValueError as exc:
        temporal = {
            "available": False,
            "reason": str(exc),
            "purpose": "No temporal partition analysis was run for this dataset.",
        }

    return {
        "report_version": "1.0",
        "method": "rule_based_water_stress_sensitivity",
        "dataset_window": _window(rows),
        "ground_truth_available": False,
        "predictive_accuracy_assessed": False,
        "accuracy_metrics": None,
        "interpretation": (
            "Results describe how index scores change under alternative assumptions; "
            "they do not measure drought-prediction accuracy."
        ),
        "caveats": [
            "The index is not a drought probability or locally validated diagnosis.",
            "Alternative configurations are sensitivity scenarios, not fitted models.",
            "Independent reference labels are required before predictive accuracy can be assessed.",
        ],
        "baseline_summary": summarize_scores(baseline),
        "scenarios": scenario_results,
        "time_aware_analysis": temporal,
    }
