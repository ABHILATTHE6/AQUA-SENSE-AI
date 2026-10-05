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

**Day 5 — Historical weather ingestion and daily training-input layer complete**

Current data flow:

`Open-Meteo Forecast API → forecast observations`

`Open-Meteo Historical API → raw reanalysis → canonical hourly observations → daily model inputs`

Next: **Day 6 — Data quality profiling and leakage-safe feature engineering**

## Day 4 Quickstart

The forecast connector requests:

- precipitation → `rainfall_mm`
- `temperature_2m` → `air_temperature_c`
- `relative_humidity_2m` → `relative_humidity_pct`
- `et0_fao_evapotranspiration` → `et0_mm`
- `soil_moisture_0_to_1cm` → `soil_moisture_m3_m3`

Run:

```bash
python scripts/ingest_open_meteo.py --location demo_location --forecast-days 3
```

## Day 5 Historical Ingestion

Historical extraction is bounded to 366 days per request:

```bash
python scripts/ingest_historical_weather.py \
  --location demo_location \
  --start-date 2026-09-01 \
  --end-date 2026-09-30
```

Outputs:

```text
data/raw/open_meteo_historical/<start-date>/batch.json
data/processed/<location_id>/hourly/<start>_<end>.jsonl
data/processed/<location_id>/daily/<start>_<end>.jsonl
```

The daily layer contains rainfall sum, mean temperature, mean relative humidity, ET₀ sum, and mean near-surface soil moisture. Days without a complete set of 24 hourly values are excluded rather than silently imputed.

All committed fixtures are synthetic and exist only for deterministic tests. Live provider access occurs when the CLI is run.
