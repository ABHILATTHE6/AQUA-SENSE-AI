# Canonical Variable Catalog

**Contract version:** 0.2.0

The canonical catalog prevents source-specific field names and units from leaking into downstream analytics. Raw source fields must be mapped into these stable names before entering the validated layer.

| Canonical variable | Meaning | Canonical unit | Minimum | Maximum | Typical grain |
|---|---|---|---:|---:|---|
| rainfall_mm | Precipitation accumulated over the observation interval | mm | 0 | — | hourly/daily |
| air_temperature_c | Near-surface air temperature | degC | -80 | — | hourly/daily |
| relative_humidity_pct | Relative humidity | pct | 0 | 100 | hourly/daily |
| et0_mm | Reference evapotranspiration over the observation interval | mm | 0 | — | daily |
| soil_moisture_m3_m3 | Volumetric soil moisture | m3/m3 | 0 | 1 | hourly/daily |
| groundwater_depth_m | Depth to groundwater below ground level | m | 0 | — | periodic |
| irrigation_demand_mm | Estimated crop irrigation requirement | mm | 0 | — | daily |

## Contract Rules

### Identity

Each observation must represent one source, one location, one timestamp, and one variable. A recommended deterministic identity key is:

source + location_id + observed_at + variable

A later ingestion service can hash this key into a compact observation ID.

### Time

- Store observed_at as an ISO-8601 timestamp.
- Preserve the source timezone when available.
- Record any timezone conversion or temporal aggregation in metadata.

### Location

- location_id is the stable internal identifier.
- Latitude and longitude are optional on the observation record because some sources will use a separate location dimension.

### Quality flags

- observed: directly reported measurement.
- estimated: provider-generated estimate.
- imputed: value filled by our pipeline.
- suspect: retained for traceability but triggered a quality rule.
- missing: placeholder state; downstream models should normally exclude it.

### Modeling guardrail

No feature may use an observation after the prediction cutoff. Time-aware splits and explicit lag construction are mandatory for later modeling work.
