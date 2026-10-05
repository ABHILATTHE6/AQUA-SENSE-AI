# Historical Weather Ingestion

## Purpose

Day 5 introduces a reproducible historical weather pipeline for building training inputs. Forecast data supports future decisions; historical sequences are required for seasonal baselines, lagged features, evaluation targets, and time-aware model validation.

## Provider Contract

The Open-Meteo Historical Weather API exposes `/v1/archive` with latitude, longitude, start date, end date, and hourly-variable parameters. Its historical service provides reanalysis datasets including ERA5 and ERA5-Land. Variable availability differs by model, so the first AQUA-SENSE extraction uses ERA5 for the five-variable canonical contract.

## Data Flow

`Historical API → raw provider payload → canonical hourly observations → daily model-input JSONL`

Raw payloads remain provider-native and are retained before transformation. Canonical observations use the same contract as the forecast connector, keeping downstream feature engineering source-agnostic.

## Daily Aggregation

The daily layer contains:

| Feature | Aggregation |
| --- | --- |
| `rainfall_mm_sum` | hourly sum |
| `air_temperature_c_mean` | hourly mean |
| `relative_humidity_pct_mean` | hourly mean |
| `et0_mm_sum` | hourly sum |
| `soil_moisture_m3_m3_mean` | hourly mean |

A daily row is created only when each required variable has the expected 24 hourly values. Missing hours are not silently filled.

## CLI

```bash
python scripts/ingest_historical_weather.py \
  --location demo_location \
  --start-date 2026-09-01 \
  --end-date 2026-09-30
```

The request is limited to 366 days to prevent accidental high-volume extraction.

## Modeling Boundary

The daily dataset is a **feature-input layer**, not a prediction. Day 6 will profile missingness and distributions, then introduce lag/rolling features while preserving chronological ordering and avoiding future-data leakage.

## Data Semantics

Historical reanalysis values are treated as `estimated` rather than direct local-station observations. This preserves honest uncertainty in the data lineage.
