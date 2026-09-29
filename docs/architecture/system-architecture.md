# System Architecture

AQUA-SENSE AI uses a layered architecture so data ingestion, transformation, modeling, inference, and presentation remain independently testable.

```text
┌───────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                     │
│  Weather · Rainfall · Soil Moisture · Groundwater · Crops   │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌───────────────────────────────────────────────────────────────┐
│                    INGESTION / CONNECTORS                    │
│      API clients · file loaders · source metadata            │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌───────────────────────────────────────────────────────────────┐
│                    DATA QUALITY LAYER                        │
│ schema checks · missing values · range checks · duplicates  │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌───────────────────────────────────────────────────────────────┐
│                STORAGE / ANALYTICS FOUNDATION                │
│              PostgreSQL + PostGIS (planned)                  │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌───────────────────────────────────────────────────────────────┐
│                  FEATURE ENGINEERING                         │
│ lags · rolling statistics · anomalies · spatial features    │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌──────────────────────────────┴────────────────────────────────┐
│                  MODELING / INTELLIGENCE                     │
│ Forecasting · anomaly detection · demand estimation         │
└──────────────────────────────┬────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                v              v              v
          Predictions        XAI         Scenario Engine
                │              │              │
                └──────────────┼──────────────┘
                               v
┌───────────────────────────────────────────────────────────────┐
│                API / DECISION SUPPORT UI                     │
│ risk map · forecasts · drivers · scenarios · data quality   │
└───────────────────────────────────────────────────────────────┘
```

## Architecture Principles

### Raw Layer
Keep source observations close to their original representation with source, collection timestamp, and metadata.

### Validated Layer
Apply deterministic checks for types, ranges, missingness, duplicates, timestamp consistency, and spatial identifiers.

### Feature Layer
Construct model-ready features without using future observations. Every feature must have an explicit definition and time reference.

### Model Layer
Keep training separate from inference. Store model version, feature version, training period, validation method, and evaluation metrics.

### Presentation Layer
Expose measured observations, model forecasts, explanations, and simulations as visually distinct concepts.

## Planned Core Services

- ingestion
- validation
- features
- models
- inference
- api
- dashboard
