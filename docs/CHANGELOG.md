# Changelog

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
