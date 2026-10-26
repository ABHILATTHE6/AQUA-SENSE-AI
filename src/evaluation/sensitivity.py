"""Descriptive sensitivity analysis for the rule-based water-stress baseline.

No predictive accuracy is reported because this workflow has no independent
ground-truth target wired into it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from statistics import mean, median
from typing import Any

from src.evaluation.time_split import chronological_split
from src.scoring.water_stress import StressConfig, score_dataset


CATEGORIES = ("low", "moderate", "high", "very_high")


def _scenario_configs() -> list[tuple[str, str, StressConfig]]:
    baseline = StressConfig()
    return [
        ("baseline_v1", "Current documented default configuration.", baseline),
        (
            "equal_weights",
            "Equal contribution from rainfall, soil moisture, ET0 and heat.",
            replace(
                baseline,
                rainfall_weight=0.25,
                soil_moisture_weight=0.25,
                et0_weight=0.25,
                heat_weight=0.25,
            ),
        ),
        (
            "soil_moisture_emphasis",
            "Higher weight on near-surface soil-moisture deficit.",
            replace(
                baseline,
                rainfall_weight=0.15,
                soil_moisture_weight=0.50,
                et0_weight=0.20,
                heat_weight=0.15,
            ),
        ),
        (
            "atmospheric_demand_emphasis",
            "Higher combined weight on ET0 and heat signals.",
            replace(
                baseline,
                rainfall_weight=0.20,
                soil_moisture_weight=0.25,
                et0_weight=0.35,
                heat_weight=0.20,
            ),
        ),
        (
            "tighter_upper_thresholds",
            "Alternative upper thresholds to test calibration sensitivity.",
            replace(
                baseline,
                rainfall_wet_mm=15.0,
                soil_moisture_wet=0.35,
                et0_high_mm=7.0,
                temperature_high_c=38.0,
            ),
        ),
    ]


def summarize_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize score distribution without implying predictive performance."""
    if not scores:
        return {
            "count": 0,
            "mean_score": None,
            "median_score": None,
            "min_score": None,
            "max_score": None,
            "category_counts": {category: 0 for category in CATEGORIES},
        }
    values = [float(row["water_stress_index"]) for row in scores]
    counts = Counter(row["water_stress_category"] for row in scores)
    return {
        "count": len(scores),
        "mean_score": round(mean(values), 3),
        "median_score": round(median(values), 3),
        "min_score": round(min(values), 3),
        "max_score": round(max(values), 3),
        "category_counts": {category: counts.get(category, 0) for category in CATEGORIES},
    }


def compare_scores(
    baseline_scores: list[dict[str, Any]],
    comparison_scores: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure score/category sensitivity for identical observations."""
    if len(baseline_scores) != len(comparison_scores):
        raise ValueError("score collections must have equal length for comparison")
    if not baseline_scores:
        raise ValueError("cannot compare empty score collections")
    baseline_by_key = {
        (row.get("date"), row.get("location_id")): row for row in baseline_scores
    }
    comparison_by_key = {
        (row.get("date"), row.get("location_id")): row for row in comparison_scores
    }
    if baseline_by_key.keys() != comparison_by_key.keys():
        raise ValueError("score collections must cover the same date/location observations")

    absolute_deltas: list[float] = []
    category_changes = 0
    for key, baseline in baseline_by_key.items():
        compared = comparison_by_key[key]
        absolute_deltas.append(
            abs(float(compared["water_stress_index"]) - float(baseline["water_stress_index"]))
        )
        if compared["water_stress_category"] != baseline["water_stress_category"]:
            category_changes += 1
    count = len(baseline_by_key)
    return {
        "mean_absolute_score_shift": round(mean(absolute_deltas), 3),
        "max_absolute_score_shift": round(max(absolute_deltas), 3),
        "category_changes": category_changes,
        "category_change_rate_pct": round(100.0 * category_changes / count, 2),
    }


def _date_window(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted(str(row["date"])[:10] for row in rows)
    return {
        "start_date": dates[0] if dates else None,
        "end_date": dates[-1] if dates else None,
        "unique_dates": len(set(dates)),
        "row_count": len(rows),
    }


def build_sensitivity_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a deterministic baseline-versus-configuration report."""
    if not rows:
        raise ValueError("input dataset has no daily records")

    scenarios = _scenario_configs()
    baseline_scores = score_dataset(rows, scenarios[0][2])
    report_scenarios: list[dict[str, Any]] = []
    for scenario_id, description, config in scenarios:
        scores = score_dataset(rows, config)
        report_scenarios.append(
            {
                "scenario_id": scenario_id,
                "description": description,
                "configuration": asdict(config),
                "summary": summarize_scores(scores),
                "comparison_to_baseline": compare_scores(baseline_scores, scores),
            }
        )

    try:
        partitions = chronological_split(rows)
        partition_reports: dict[str, Any] = {}
        for partition_name, partition_rows in partitions.items():
            partition_baseline = score_dataset(partition_rows)
            partition_scenarios: dict[str, Any] = {}
            for scenario_id, _, config in scenarios:
                partition_scores = score_dataset(partition_rows, config)
                partition_scenarios[scenario_id] = {
                    "summary": summarize_scores(partition_scores),
                    "comparison_to_baseline": compare_scores(
                        partition_baseline, partition_scores
                    ),
                }
            partition_reports[partition_name] = {
                "window": _date_window(partition_rows),
                "baseline_summary": summarize_scores(partition_baseline),
                "scenarios": partition_scenarios,
            }
        time_analysis: dict[str, Any] = {
            "available": True,
            "purpose": (
                "Descriptive sensitivity by chronological period only; these partitions "
                "are not predictive model evaluation results."
            ),
            "partitions": partition_reports,
        }
    except ValueError as exc:
        time_analysis = {
            "available": False,
            "reason": str(exc),
            "purpose": "No temporal partition metrics were computed for this input.",
        }

    return {
        "report_version": "1.0",
        "method": "rule_based_water_stress_sensitivity",
        "dataset_window": _date_window(rows),
        "ground_truth_available": False,
        "predictive_accuracy_assessed": False,
        "accuracy_metrics": None,
        "interpretation": (
            "This report measures how the exploratory index changes under alternative "
            "weights and thresholds. It does not measure drought-prediction accuracy."
        ),
        "caveats": [
            "The index is not a drought probability or a locally validated diagnosis.",
            "The alternatives are sensitivity scenarios, not fitted or optimized models.",
            "An independent reference target is required before predictive performance can be assessed.",
        ],
        "baseline_summary": summarize_scores(baseline_scores),
        "scenarios": report_scenarios,
        "time_aware_analysis": time_analysis,
    }
