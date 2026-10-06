# Data Quality & Feature Engineering

## Day 6 goal

Turn the daily weather layer into trustworthy model inputs without hiding data problems or leaking future information.

## Quality profiling

`profile_daily_dataset()` reports:

- row and unique-date counts
- duplicate dates
- missing calendar days
- complete-hourly-day count
- missing numeric values
- minimum, maximum, mean, quartiles, IQR, and Tukey outlier counts

The profiler is intentionally observational. It **does not** fill missing values, remove outliers, or rewrite source data.

## Feature engineering

The feature builder adds:

- 1/3/7-day exact calendar lags
- prior 3/7-day rolling features where appropriate
- rainfall and ET₀ cumulative windows
- temperature, humidity, and soil-moisture rolling means

For a target row dated **D**, every engineered value comes only from dates **before D**.

### Leakage controls

1. Current-day values are never included in rolling windows.
2. Lag features require the exact calendar offset.
3. Rolling windows require every prior calendar day to exist.
4. No imputation occurs in the feature builder.
5. Duplicate daily dates are rejected.

These rules are designed to preserve chronological causality for later water-stress forecasting experiments.

## CLI workflow

```bash
python scripts/profile_daily_weather.py --input <daily.jsonl>

python scripts/engineer_daily_features.py \
  --input <daily.jsonl> \
  --output <features.jsonl>
```

## Modeling boundary

Day 6 stops at feature preparation. It does not create a water-stress target or train a model. Day 7 will define a transparent target/index before any predictive algorithm is evaluated.
