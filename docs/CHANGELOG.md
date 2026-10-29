# Changelog

## Day 10 — Karnataka Groundwater Reference Acquisition & Quality Review

- Added a streaming CSV acquisition path for Karnataka Ground Water Department telemetry published through the National Water Data Portal.
- Added header-resilient normalization into the reference-target contract, retaining station metadata, optional coordinates, explicit timezone assumptions, and candidate-only independence status.
- Added SHA-256 provenance, a download-size cap, raw-file preservation, offline processing mode, and a CLI row limit for smoke checks.
- Added a streaming quality profile for coverage, station and district counts, timestamp span, coordinate completeness, depth range, and rejection reasons.
- Added duplicate station/timestamp detection and rejected-row quarantine instead of silent imputation or correction.
- Added source and reference-target registry entries, a synthetic CSV fixture, tests, and acquisition documentation.
- No source data are stored in Git; predictive accuracy remains unassessed pending target-suitability and alignment review.


## Day 9 — Independent Reference Target & Forecasting Readiness

- Added a machine-readable reference-target contract for sourced numeric measurements and categorical assessments.
- Added validation for timezone-aware timestamps, source identity, target variable/unit compatibility, finite values, spatial/temporal support, and review provenance.
- Added a mechanical independence screen that flags shared source or target-concept overlap against model inputs.
- Registered NASA SMAP, CGWB groundwater monitoring, official drought classifications, and local field assessments as candidates with explicit usage limitations.
- Documented that source independence alone does not establish target validity and that component-level soil-moisture comparison is not full-index ground truth.
- Added deterministic tests for valid targets, invalid units/ranges, missing review metadata, and overlap safeguards.
- No external reference observations were downloaded or treated as ground truth in this step.

## Day 8 — Baseline Evaluation & Time-Aware Comparison

- Added chronological train/validation/test partitioning based on unique calendar dates; all locations from the same day remain in one partition.
- Rejected duplicate date/location observations and invalid or too-short time windows rather than silently splitting them.
- Added a deterministic sensitivity report comparing the default water-stress index with alternative weight and threshold configurations.
- Reported score distribution, category counts, mean/max absolute score shifts, and category-change rates.
- Added descriptive sensitivity summaries for chronological periods when at least three unique dates are available.
- Explicitly disclosed that no independent ground-truth target is available and predictive accuracy has not been assessed.
- Added a JSON report CLI, automated tests, and an evaluation-protocol document.

## Day 7 — Water-Stress Target Definition & Transparent Baseline Index

- Defined an explicitly exploratory 0–100 rule-based water-stress screening index.
- Added rainfall-deficit, soil-moisture-deficit, evaporative-demand, and heat components with documented default weights.
- Exposed component scores and weighted contributions for interpretation.
- Added configurable thresholds and weight-sum validation.
- Added strict input checks for missing/non-finite values, negative rainfall/ET₀, and out-of-range soil moisture.
- Added a JSONL CLI for scoring daily weather records.
- Added tests for dry/hot versus wet/cool cases, score bounds, explanation fields, and invalid inputs.
- Documented that the index is not a drought probability and requires local calibration before operational use.

## Day 6 — Data Quality Profiling & Leakage-Safe Features

- Added a deterministic daily-data quality profiler with row counts, date coverage, duplicates, calendar gaps, completeness, and numeric distribution statistics.
- Added Tukey IQR outlier counts as review signals rather than automatic corrections.
- Added explicit review flags for duplicate dates, calendar gaps, missing values, and IQR outliers.
- Added leakage-safe lag features at 1, 3, and 7 days for core weather variables.
- Added prior-window rolling statistics while excluding the current observation from every window.
- Required complete prior calendar windows for rolling features so gaps do not masquerade as continuous history.
- Added CLI tools for profiling datasets and generating feature JSONL outputs.
- Added tests proving current-day values cannot leak into rolling features and that calendar gaps suppress invalid windows.

## Day 5 — Historical Weather & Training Input Layer

- Added a bounded Open-Meteo Historical Weather API adapter using the `/v1/archive` endpoint.
- Added configurable historical date ranges and reanalysis model selection with a 366-day safety bound.
- Added canonical normalization for temperature, relative humidity, precipitation, ET₀, and near-surface soil moisture.
- Preserved raw reanalysis payloads with ingestion provenance.
- Added a daily aggregation layer for model inputs: sums for rainfall/ET₀ and means for state variables.
- Excluded incomplete hourly days instead of silently imputing missing values.
- Added a historical ingestion CLI and deterministic fixture-based tests.
- Documented the historical data and modeling boundary.

## Day 4 — First Real Weather Ingestion Connector

- Implemented an Open-Meteo Forecast API adapter using Python's standard-library HTTP stack.
- Added provider-to-canonical mappings for precipitation, temperature, humidity, ET₀, and near-surface soil moisture.
- Added deterministic UTC timestamp normalization and `estimated` quality semantics for forecast values.
- Added raw provider payload capture with provenance through the existing `RawRecord` contract.
- Added processed JSONL persistence for validated canonical observations.
- Added a command-line ingestion entry point driven by `config/locations.json`.
- Added deterministic fixture-based tests covering URL construction, response validation, normalization, provenance, adapter behavior, and end-to-end layer persistence.
- Upgraded CI to install pytest and execute the test suite on pushes and pull requests.

## Day 3 — Data Registry & Ingestion Skeleton

- Added a machine-readable source registry for initial weather, soil-moisture, and groundwater sources.
- Added a source-agnostic `SourceAdapter` contract and raw-record provenance model.
- Added deterministic raw-data partitioning and JSON batch storage helpers.
- Documented raw, processed, sample, schema, and contract data layers.
- Added ingestion unit tests.

## Day 2 — Data Contract & Canonical Schema

- Upgraded the observation schema with a controlled canonical variable vocabulary.
- Defined canonical units, ranges, time-grain expectations, identity rules, and quality semantics.
- Added source-to-canonical mapping guidance and required ingestion metadata.
- Added a standard-library validator for application-level ingestion guardrails.
- Added validation tests for valid data and common contract violations.
- Added project packaging and pytest configuration.

## Day 1 — Project Foundation

- Established AQUA-SENSE AI project identity and scope.
- Added project charter with goals, non-goals, success criteria, and risks.
- Added layered system architecture.
- Added development roadmap.
- Added initial canonical environmental observation JSON Schema.
- Added CI scaffold.
