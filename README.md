# AQUA-SENSE AI

**AI-Powered Local Water Stress & Smart Irrigation Intelligence Platform**

AQUA-SENSE AI is an end-to-end AI/Data Science platform designed to analyze environmental conditions, explain water-stress signals, and support informed water and irrigation decisions.

## Core question

**Where is water stress increasing, why might it be increasing, and what could happen under alternative scenarios?**

## Architecture

`External Data → Ingestion → Raw Storage → Validation → Feature Engineering → Baseline/ML → Explainability → Scenario Engine → API/Dashboard`

## Engineering principles

1. Evidence before modeling
2. Baseline before complexity
3. Reproducibility
4. Explainability
5. No false precision
6. Decision support, not autonomous control

## Development status

**Day 7 — Explainable rule-based water-stress baseline complete**

Current flow:

`Open-Meteo → raw/reanalysis → canonical observations → daily inputs → quality profile → leakage-safe features → rule-based stress index`

Next: **Day 8 — Baseline evaluation protocol and time-aware comparison**

## Historical ingestion

```bash
python scripts/ingest_historical_weather.py \
  --location demo_location \
  --start-date 2026-09-01 \
  --end-date 2026-09-30
```

## Quality profiling

```bash
python scripts/profile_daily_weather.py --input <daily.jsonl>
```

## Leakage-safe features

```bash
python scripts/engineer_daily_features.py \
  --input <daily.jsonl> \
  --output <features.jsonl>
```

## Water-stress baseline

```bash
python scripts/score_water_stress.py \
  --input <daily.jsonl> \
  --output <stress_scores.jsonl>
```

### Baseline components

| Component | Direction | Default weight |
| --- | --- | ---: |
| Rainfall deficit | Less rainfall → higher stress | 0.25 |
| Soil-moisture deficit | Drier soil → higher stress | 0.35 |
| Evaporative demand | Higher ET₀ → higher stress | 0.25 |
| Heat | Higher mean temperature → higher stress | 0.15 |

Each component is clamped to 0–1 and combined into a 0–100 **relative screening index**. Scores are not drought probabilities and are not calibrated operational thresholds. The defaults are transparent assumptions for a first baseline; local validation and domain input are required before decision use.

All committed fixtures are synthetic and used for deterministic tests. Live provider access occurs when ingestion commands are run.
