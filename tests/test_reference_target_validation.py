import pytest

from src.validation.reference_target import (
    ReferenceTargetValidationError,
    assess_target_independence,
    validate_reference_target,
)


def reference(**overrides):
    record = {
        "reference_id": "demo-target-001",
        "observed_at": "2026-09-01T12:00:00+00:00",
        "location_id": "demo_location",
        "source": "field_observations",
        "target_variable": "field_water_stress_assessment",
        "value": "moderate",
        "unit": "category",
        "temporal_support": "daily",
        "spatial_support": {"kind": "point", "spatial_id": "plot-01"},
        "quality_flag": "observed",
        "independence_assessment": {
            "status": "approved",
            "notes": "Independently collected using a documented field protocol.",
            "reviewer": "hydrology-review",
            "reviewed_at": "2026-09-05T10:00:00+00:00",
        },
    }
    record.update(overrides)
    return record


def test_accepts_a_documented_categorical_field_reference():
    validate_reference_target(reference())


def test_rejects_naive_datetime_without_timezone():
    with pytest.raises(ReferenceTargetValidationError, match="timezone offset"):
        validate_reference_target(reference(observed_at="2026-09-01T12:00:00"))


def test_rejects_reference_unit_mismatch():
    with pytest.raises(ReferenceTargetValidationError, match="requires unit category"):
        validate_reference_target(reference(unit="index"))


def test_rejects_invalid_surface_soil_moisture_range():
    record = reference(
        target_variable="surface_soil_moisture_m3_m3",
        value=1.2,
        unit="m3/m3",
    )
    with pytest.raises(ReferenceTargetValidationError, match="between 0 and 1"):
        validate_reference_target(record)


def test_approved_record_requires_reviewer_and_review_time():
    assessment = {"status": "approved", "notes": "Reviewed but missing reviewer details."}
    with pytest.raises(ReferenceTargetValidationError, match="require independence_assessment.reviewer"):
        validate_reference_target(reference(independence_assessment=assessment))


def test_smap_like_target_is_component_reference_not_composite_index_target():
    record = reference(
        source="nasa_smap",
        target_variable="surface_soil_moisture_m3_m3",
        value=0.22,
        unit="m3/m3",
        spatial_support={"kind": "grid_cell", "resolution_km": 9.0},
        independence_assessment={
            "status": "candidate",
            "notes": "Independent sensor source; construct overlaps the index component.",
        },
    )
    report = assess_target_independence(
        record,
        model_input_sources={"open_meteo"},
        model_input_variables={"soil_moisture_m3_m3", "rainfall_mm"},
    )
    assert report["source_independent"] is True
    assert report["construct_independent"] is False
    assert report["eligible_for_evaluation_screen"] is False


def test_same_source_and_suspect_quality_fail_independence_screen():
    record = reference(
        source="open_meteo",
        quality_flag="suspect",
        independence_assessment={
            "status": "candidate",
            "notes": "Not independently verified.",
        },
    )
    report = assess_target_independence(
        record,
        model_input_sources={"open_meteo"},
        model_input_variables=set(),
    )
    assert report["source_independent"] is False
    assert report["quality_acceptable"] is False
    assert report["eligible_for_evaluation_screen"] is False
