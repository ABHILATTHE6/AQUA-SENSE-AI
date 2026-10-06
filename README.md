# AQUA-SENSE AI

**AI-Powered Local Water Stress & Smart Irrigation Intelligence Platform**

AQUA-SENSE AI is an end-to-end Artificial Intelligence and Data Science platform designed to forecast local water stress, explain the factors driving the forecast, simulate what-if scenarios, and support data-informed water and irrigation decisions.

## Core Problem

Water stress is influenced by rainfall variability, soil moisture, temperature, evapotranspiration, groundwater trends, and agricultural demand.

> **Where is water stress increasing, why is it increasing, and what could happen under alternative scenarios?**

## Architecture

`External Data → Ingestion → Raw Storage → Validation → Feature Engineering → ML → XAI → Scenario Engine → API/Dashboard`

## Engineering Principles

1. Evidence before modeling
2. Baseline before complexity
3. Reproducibility
4. Explainability
5. No false precision
6. Decision support, not autonomous control

## Development Status

**Day 6 — Data quality profiling and leakage-safe feature engineering complete**

Current flow:

`Open-Meteo Historical API → raw reanalysis → canonical hourly observations → daily model inputs → quality profile → lag/rolling features`

Next: **Day 7 — Water-stress target definition and transparent baseline index**

## Day 5 Historical Ingestion

```bash
python scripts/ingest_historical_weather.py \
  --location demo_location \
  --start-date 2026-09-01 \
  --end-date 2026-09-30
```

## Day 6 Quality & Features

Profile a daily JSONL dataset:

```bash
python scripts/profile_daily_weather.py \
  --input data/processed/demo_location/daily/2026-09-01_2026-09-30.jsonl
```

Create leakage-safe features:

```bash
python scripts/engineer_daily_features.py \
  --input data/processed/demo_location/daily/2026-09-01_2026-09-30.jsonl \
  --output data/processed/demo_location/features/2026-09-01_2026-09-30.jsonl
```

Feature engineering rules:

- lag features use exact prior calendar days
- rolling windows exclude the current day
- incomplete calendar windows produce `null`, not fabricated values
- quality profiling reports gaps, duplicates, missingness, and IQR outliers without auto-correction

All committed fixtures are synthetic and exist only for deterministic tests. Live provider access occurs when the ingestion CLI is run.
