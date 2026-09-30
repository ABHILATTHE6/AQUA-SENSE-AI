# Data Directory

## Layers

- `raw/` — immutable provider-native ingestion artifacts. Never manually edit these files.
- `processed/` — validated and normalized records ready for analytical transformation.
- `samples/` — tiny synthetic or deliberately selected examples used for tests and documentation.
- `schemas/` — machine-readable data contracts.
- `contracts/` — human-readable data semantics and rules.

## Partition Convention

Raw files are partitioned as:

`raw/<source_id>/<YYYY-MM-DD>/batch.json`

Provider payloads remain unchanged inside the raw layer. Normalization belongs in the validated/processed pipeline.

## Data Safety

Large raw datasets are not committed to Git. `.gitignore` excludes raw and processed data by default. Small synthetic fixtures may be committed under `samples/`.
