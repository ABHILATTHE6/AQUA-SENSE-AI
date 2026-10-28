"""Validation and independence checks for AQUA-SENSE reference targets."""

from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any


TARGET_UNITS = {
    "surface_soil_moisture_m3_m3": "m3/m3",
    "groundwater_depth_m": "m",
    "vegetation_health_anomaly": "index",
    "official_drought_classification": "category",
    "field_water_stress_assessment": "category",
}
CATEGORICAL_TARGETS = {"official_drought_classification", "field_water_stress_assessment"}
INDEPENDENCE_STATUSES = {"not_assessed", "candidate", "approved", "rejected"}
QUALITY_FLAGS = {"observed", "estimated", "suspect"}
TARGET_INPUT_CONCEPTS = {
    "surface_soil_moisture_m3_m3": {"soil_moisture_m3_m3", "surface_soil_moisture"},
    "groundwater_depth_m": {"groundwater_depth_m", "groundwater_depth"},
    "vegetation_health_anomaly": {"vegetation_health_anomaly", "vegetation_index"},
    "official_drought_classification": {"official_drought_classification"},
    "field_water_stress_assessment": {"field_water_stress_assessment"},
}


class ReferenceTargetValidationError(ValueError):
    """Raised when a reference target violates its data contract."""


def _require_non_empty_string(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ReferenceTargetValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _parse_timezone_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ReferenceTargetValidationError(f"{field} must be an ISO-8601 datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReferenceTargetValidationError(
            f"{field} must be a valid ISO-8601 datetime"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReferenceTargetValidationError(f"{field} must include a timezone offset")
    return parsed


def validate_reference_target(record: dict[str, Any]) -> None:
    """Validate one target record. This cannot prove scientific target validity."""
    if not isinstance(record, dict):
        raise ReferenceTargetValidationError("reference target must be an object")

    required = {
        "reference_id", "observed_at", "location_id", "source",
        "target_variable", "value", "unit", "temporal_support",
        "spatial_support", "quality_flag", "independence_assessment",
    }
    missing = required - record.keys()
    if missing:
        raise ReferenceTargetValidationError(
            f"missing required fields: {', '.join(sorted(missing))}"
        )

    for field in ("reference_id", "location_id", "source", "unit"):
        _require_non_empty_string(record, field)
    _parse_timezone_datetime(record["observed_at"], "observed_at")

    target_variable = record["target_variable"]
    if target_variable not in TARGET_UNITS:
        raise ReferenceTargetValidationError(f"unsupported target_variable: {target_variable}")
    expected_unit = TARGET_UNITS[target_variable]
    if record["unit"] != expected_unit:
        raise ReferenceTargetValidationError(
            f"{target_variable} requires unit {expected_unit}, got {record['unit']}"
        )

    value = record["value"]
    if target_variable in CATEGORICAL_TARGETS:
        if not isinstance(value, str) or not value.strip():
            raise ReferenceTargetValidationError(
                f"{target_variable} value must be a non-empty source label"
            )
    else:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ReferenceTargetValidationError("numeric target value must be finite")
        if target_variable == "surface_soil_moisture_m3_m3" and not 0 <= value <= 1:
            raise ReferenceTargetValidationError(
                "surface_soil_moisture_m3_m3 value must be between 0 and 1"
            )
        if target_variable == "groundwater_depth_m" and value < 0:
            raise ReferenceTargetValidationError("groundwater_depth_m value must be non-negative")

    supported_temporal = {
        "instantaneous", "daily", "weekly", "monthly", "seasonal", "irregular"
    }
    if record["temporal_support"] not in supported_temporal:
        raise ReferenceTargetValidationError("unsupported temporal_support")

    spatial = record["spatial_support"]
    if not isinstance(spatial, dict):
        raise ReferenceTargetValidationError("spatial_support must be an object")
    if spatial.get("kind") not in {"point", "grid_cell", "administrative_area"}:
        raise ReferenceTargetValidationError("unsupported spatial_support.kind")
    if "resolution_km" in spatial:
        resolution = spatial["resolution_km"]
        if (
            isinstance(resolution, bool)
            or not isinstance(resolution, (int, float))
            or not isfinite(resolution)
            or resolution <= 0
        ):
            raise ReferenceTargetValidationError("resolution_km must be a positive finite number")
    if spatial["kind"] == "grid_cell" and "resolution_km" not in spatial:
        raise ReferenceTargetValidationError("grid_cell spatial support requires resolution_km")

    if record["quality_flag"] not in QUALITY_FLAGS:
        raise ReferenceTargetValidationError("unsupported quality_flag")

    assessment = record["independence_assessment"]
    if not isinstance(assessment, dict):
        raise ReferenceTargetValidationError("independence_assessment must be an object")
    status = assessment.get("status")
    if status not in INDEPENDENCE_STATUSES:
        raise ReferenceTargetValidationError("unsupported independence_assessment.status")
    notes = assessment.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise ReferenceTargetValidationError("independence_assessment.notes must be non-empty")
    if status == "approved":
        reviewer = assessment.get("reviewer")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ReferenceTargetValidationError(
                "approved reference targets require independence_assessment.reviewer"
            )
        _parse_timezone_datetime(
            assessment.get("reviewed_at"), "independence_assessment.reviewed_at"
        )


def assess_target_independence(
    record: dict[str, Any],
    *,
    model_input_sources: set[str],
    model_input_variables: set[str],
) -> dict[str, Any]:
    """Screen for source/construct overlap against declared model inputs.

    Passing the screen is not proof of scientific validity; domain review remains
    required even if source and construct are distinct.
    """
    validate_reference_target(record)
    source_independent = record["source"] not in model_input_sources
    target_variable = record["target_variable"]
    overlapping_concepts = sorted(
        TARGET_INPUT_CONCEPTS[target_variable].intersection(model_input_variables)
    )
    construct_independent = not overlapping_concepts
    review_approved = record["independence_assessment"]["status"] == "approved"
    quality_acceptable = record["quality_flag"] in {"observed", "estimated"}
    eligible = (
        source_independent and construct_independent
        and review_approved and quality_acceptable
    )
    return {
        "source_independent": source_independent,
        "construct_independent": construct_independent,
        "overlapping_input_concepts": overlapping_concepts,
        "review_approved": review_approved,
        "quality_acceptable": quality_acceptable,
        "eligible_for_evaluation_screen": eligible,
        "warning": (
            "Mechanical screening only; target definition, temporal and spatial alignment, "
            "and domain suitability still require human review."
        ),
    }
