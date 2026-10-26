"""Transparent, rule-based water-stress baseline for AQUA-SENSE AI.

This is an exploratory indicator, not a validated drought diagnosis. Its score
is designed for explainable relative screening and must be calibrated against
local agronomic/hydrological evidence before operational use.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class StressConfig:
    """Documented normalization thresholds for the initial baseline."""

    rainfall_dry_mm: float = 0.0
    rainfall_wet_mm: float = 10.0
    et0_low_mm: float = 2.0
    et0_high_mm: float = 8.0
    soil_moisture_dry: float = 0.10
    soil_moisture_wet: float = 0.40
    temperature_low_c: float = 20.0
    temperature_high_c: float = 40.0
    rainfall_weight: float = 0.25
    soil_moisture_weight: float = 0.35
    et0_weight: float = 0.25
    heat_weight: float = 0.15

    def validate(self) -> None:
        thresholds = (
            (self.rainfall_dry_mm, self.rainfall_wet_mm, "rainfall"),
            (self.et0_low_mm, self.et0_high_mm, "ET0"),
            (self.soil_moisture_dry, self.soil_moisture_wet, "soil moisture"),
            (self.temperature_low_c, self.temperature_high_c, "temperature"),
        )
        for low, high, label in thresholds:
            if not low < high:
                raise ValueError(f"{label} lower threshold must be below upper threshold")
        weights = (
            self.rainfall_weight,
            self.soil_moisture_weight,
            self.et0_weight,
            self.heat_weight,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("component weights must be non-negative")
        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("component weights must sum to 1.0")


def _finite_number(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    if value is None:
        raise ValueError(f"missing required field: {field}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _inverse_scale(value: float, low: float, high: float) -> float:
    """Map low resource availability to high stress, clamped to [0, 1]."""
    return max(0.0, min(1.0, (high - value) / (high - low)))


def _direct_scale(value: float, low: float, high: float) -> float:
    """Map high atmospheric demand/heat to high stress, clamped to [0, 1]."""
    return max(0.0, min(1.0, (value - low) / (high - low)))


def score_water_stress(
    row: dict[str, Any],
    config: StressConfig = StressConfig(),
) -> dict[str, Any]:
    """Score one daily record on a 0–100 relative stress scale.

    Inputs are daily rainfall sum, ET0 sum, mean soil moisture and mean
    temperature. The returned component scores and weighted contributions make
    the score auditable. This is not a probability of drought.
    """

    config.validate()
    rainfall = _finite_number(row, "rainfall_mm_sum")
    et0 = _finite_number(row, "et0_mm_sum")
    soil = _finite_number(row, "soil_moisture_m3_m3_mean")
    temperature = _finite_number(row, "air_temperature_c_mean")

    if rainfall < 0:
        raise ValueError("rainfall_mm_sum must be non-negative")
    if et0 < 0:
        raise ValueError("et0_mm_sum must be non-negative")
    if not 0.0 <= soil <= 1.0:
        raise ValueError("soil_moisture_m3_m3_mean must be between 0 and 1")

    components = {
        "rainfall_deficit": _inverse_scale(
            rainfall, config.rainfall_dry_mm, config.rainfall_wet_mm
        ),
        "soil_moisture_deficit": _inverse_scale(
            soil, config.soil_moisture_dry, config.soil_moisture_wet
        ),
        "evaporative_demand": _direct_scale(et0, config.et0_low_mm, config.et0_high_mm),
        "heat": _direct_scale(
            temperature, config.temperature_low_c, config.temperature_high_c
        ),
    }
    weights = {
        "rainfall_deficit": config.rainfall_weight,
        "soil_moisture_deficit": config.soil_moisture_weight,
        "evaporative_demand": config.et0_weight,
        "heat": config.heat_weight,
    }
    contributions = {name: components[name] * weights[name] for name in components}
    score = round(100.0 * sum(contributions.values()), 2)

    if score < 25:
        category = "low"
    elif score < 50:
        category = "moderate"
    elif score < 75:
        category = "high"
    else:
        category = "very_high"

    return {
        "date": row.get("date"),
        "location_id": row.get("location_id"),
        "water_stress_index": score,
        "water_stress_category": category,
        "component_scores": {name: round(value, 4) for name, value in components.items()},
        "weighted_contributions": {
            name: round(value, 4) for name, value in contributions.items()
        },
        "method": "rule_based_v1",
        "interpretation": "relative screening indicator; not a drought probability",
    }


def score_dataset(
    rows: list[dict[str, Any]],
    config: StressConfig = StressConfig(),
) -> list[dict[str, Any]]:
    """Score daily records independently, preserving input order."""
    return [score_water_stress(row, config) for row in rows]
