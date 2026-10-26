# Water-Stress Target Definition & Baseline Index

## Purpose and limits

Day 7 introduces a transparent, rule-based **relative water-stress screening index**. It is a baseline hypothesis for engineering and evaluation—not a validated drought diagnosis, a probability, or a locally calibrated agricultural recommendation.

The index combines four daily signals:
- rainfall deficit
- soil-moisture deficit
- reference evapotranspiration (ET₀) as a proxy for atmospheric evaporative demand
- mean air temperature as a simple heat signal

Groundwater depth, crop type, soil texture, rooting depth, irrigation, and local climate normals are not yet included. Those omissions limit interpretation, and the index must not be used as a substitute for local hydrological/agronomic assessment.

## Component normalization

Each component is normalized to [0, 1] and clamped to that range.

### Rainfall deficit

`rainfall_component = clamp((rainfall_wet - rainfall_mm_sum) / (rainfall_wet - rainfall_dry), 0, 1)`

Defaults: dry = 0 mm/day; wet = 10 mm/day.

### Soil-moisture deficit

`soil_component = clamp((soil_wet - soil_moisture) / (soil_wet - soil_dry), 0, 1)`

Defaults: dry = 0.10 m³/m³; wet = 0.40 m³/m³.

### Evaporative demand

`et0_component = clamp((ET0 - et0_low) / (et0_high - et0_low), 0, 1)`

Defaults: low = 2 mm/day; high = 8 mm/day.

### Heat

`heat_component = clamp((temperature - temperature_low) / (temperature_high - temperature_low), 0, 1)`

Defaults: low = 20 °C; high = 40 °C.

## Weighted index

`index = 100 × (0.25 × rainfall + 0.35 × soil + 0.25 × ET0 + 0.15 × heat)`

Weights sum to 1.0. Soil moisture has the largest default weight because it more directly reflects near-surface water availability than any single day's rainfall. This weighting is a transparent starting assumption, not a claim of universal scientific optimality.

Categories are provisional:
- 0 to <25: low
- 25 to <50: moderate
- 50 to <75: high
- 75 to 100: very high

## Output and explanation

Every result includes the numeric index, provisional category, normalized component scores, weighted contributions, method version, and an explicit interpretation warning. This makes the arithmetic inspectable rather than presenting a score as a black box.

## Input checks

The implementation rejects missing/non-numeric/non-finite required values, negative rainfall or ET₀, soil moisture outside [0, 1], invalid normalization thresholds, negative weights, and weights that do not sum to 1.

## Validation plan

Before operational use, thresholds and weights need review against:
1. local crop and soil context;
2. regional climate normals and seasonality;
3. independent drought/water-stress observations or accepted indicators;
4. out-of-time and out-of-location evaluation;
5. sensitivity analysis for each component and weight.

Do not interpret the current score as a drought probability. Future work should compare the rule-based index with documented reference indicators and test whether it helps decisions without overstating certainty.
