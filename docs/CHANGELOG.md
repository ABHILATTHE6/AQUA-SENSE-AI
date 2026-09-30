# Changelog

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
