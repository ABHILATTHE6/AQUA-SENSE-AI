# Source-to-Canonical Mapping

Source adapters will convert provider-native fields into the AQUA-SENSE canonical variables before validated storage.

| Source family | Example provider signal | Canonical variable | Unit | Mapping note |
|---|---|---|---|---|
| Weather API / reanalysis | precipitation / rain | rainfall_mm | mm | Preserve aggregation interval |
| Weather API / reanalysis | temperature at 2 m | air_temperature_c | degC | Record model/dataset name |
| Weather API / reanalysis | relative humidity at 2 m | relative_humidity_pct | pct | Validate 0–100 |
| Weather API / reanalysis | reference evapotranspiration ET0 | et0_mm | mm | Prefer explicit daily interval |
| Weather / remote sensing | soil moisture | soil_moisture_m3_m3 | m3/m3 | Record product and depth |
| Groundwater monitoring | depth below ground level | groundwater_depth_m | m | Preserve well identity and date |
| Agricultural dataset/model | irrigation requirement | irrigation_demand_mm | mm | Label as estimated/modelled |

## Required Source Metadata

Every ingested record should retain enough metadata to answer:

- Which provider and dataset produced the value?
- When was it retrieved?
- What was the original observation timestamp?
- What spatial unit or grid cell was used?
- What original field name and unit were mapped?
- Was conversion, aggregation, interpolation, or imputation applied?

## Initial Source Candidates

- Open-Meteo historical/forecast interfaces for weather and related variables.
- NASA SMAP products for independent soil-moisture inputs.
- Central Ground Water Board monitoring data for groundwater-level inputs.

Coverage, licensing, availability, and update behavior will be rechecked when each connector is implemented.
