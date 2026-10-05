# Open-Meteo Ingestion Connector

Day 4 establishes the first production-shaped external weather connector for AQUA-SENSE AI.

## Provider Contract

The connector targets the Open-Meteo Forecast API at:

`https://api.open-meteo.com/v1/forecast`

The request is generated from `OpenMeteoConfig` and always asks for UTC timestamps so canonical observations remain timezone-consistent.

## Provider-to-Canonical Mapping

| Open-Meteo field | AQUA-SENSE variable | Unit |
| --- | --- | --- |
| `precipitation` | `rainfall_mm` | `mm` |
| `temperature_2m` | `air_temperature_c` | `degC` |
| `relative_humidity_2m` | `relative_humidity_pct` | `pct` |
| `et0_fao_evapotranspiration` | `et0_mm` | `mm` |
| `soil_moisture_0_to_1cm` | `soil_moisture_m3_m3` | `m3/m3` |

These fields are supported by the current Open-Meteo weather API documentation and provide a useful first weather feature set for water-stress analysis.

## Pipeline

`OpenMeteoConfig → fetch_payload() → RawRecord → raw batch.json → normalize_payload() → validate_observation() → observations.jsonl`

The raw payload is retained before transformation. Canonical observations are written only after every generated row passes the existing application-level validation rules.

## Quality Semantics

Forecast values are stored with:

`quality_flag = estimated`

This avoids misrepresenting model-generated forecasts as direct field observations.

## Testing Strategy

Network calls are not required for unit tests. A deterministic provider-shaped fixture is injected into the fetch and pipeline layers. Tests cover URL construction, response-shape validation, canonical mapping, validation failures, adapter behavior, provenance preservation, and processed/raw persistence.

## Why This Design

The connector is deliberately source-specific only at the boundary. Downstream layers consume canonical observations, which means future NASA SMAP and groundwater adapters can be added without changing feature-engineering or modeling code.

Provider documentation: https://open-meteo.com/en/docs
