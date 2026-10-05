# Changelog

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
