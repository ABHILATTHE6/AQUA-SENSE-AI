# Day 8 — Baseline Evaluation & Time-Aware Comparison

## Goal

Day 8 establishes an evaluation discipline for the initial rule-based water-stress index. The aim is to measure reproducibility and sensitivity to transparent assumptions—not to overstate what the index proves.

## Important distinction: sensitivity is not accuracy

The current index is a deterministic function of daily rainfall, near-surface soil moisture, ET0, and mean temperature. The repository does not yet contain an independent, trusted target label for water stress or drought. Therefore this workflow deliberately reports **no predictive accuracy, precision, recall, R-squared, MAE, or RMSE**. Such metrics would be unjustified without a reference target and a clearly defined prediction horizon.

## Reproducible configuration scenarios

The evaluation script scores the same input rows using five documented configurations:

1. **baseline_v1** — current default thresholds and weights;
2. **equal_weights** — all four components have a weight of 0.25;
3. **soil_moisture_emphasis** — soil moisture has a weight of 0.50;
4. **atmospheric_demand_emphasis** — ET0 and heat receive greater combined weight;
5. **tighter_upper_thresholds** — an alternative set of upper normalization thresholds.

For each scenario the JSON report includes its configuration, score distribution, category counts, mean/max absolute score shift relative to the default, and the percentage of observations that change category. These are descriptive sensitivity measures, not model-selection results. The scenarios are not fitted or optimized against the input data.

## Time-aware partitions

The chronological split utility provides deterministic train/validation/test partitions for future predictive work. It sorts by calendar date and puts **every location observed on a given date into the same partition**, avoiding date overlap across split boundaries. Duplicate date/location observations are rejected. The default proportions are 70% train, 15% validation, and 15% test by unique date, subject to the minimum requirement that each partition contains at least one date.

In this Day 8 report, temporal partitions are used only to describe how index scores and configuration sensitivity vary across earlier, middle, and later periods. They are **not** presented as model training or held-out predictive evaluation, because no model is fitted and there is no independent target. Inputs with fewer than three unique dates still receive whole-dataset sensitivity results, but time-partition analysis is explicitly marked unavailable.

## Run the report

    python scripts/evaluate_water_stress_baseline.py --input <daily.jsonl> --output reports/water_stress_sensitivity.json

The command reads daily JSON Lines produced by the historical weather pipeline and writes a JSON report. The input must contain the fields required by the current scoring function: date, rainfall_mm_sum, soil_moisture_m3_m3_mean, et0_mm_sum, and air_temperature_c_mean. A location_id is used for observation identity and comparisons.

## How to interpret results

- A large mean score shift suggests the default score depends meaningfully on weight/threshold assumptions.
- A high category-change rate suggests category labels are unstable under the tested alternatives.
- Low sensitivity within this small scenario set does not prove that thresholds are scientifically valid.
- Differences between time partitions may reflect seasonal changes, incomplete coverage, or changing data quality; they are not evidence of degradation without further analysis.
- Synthetic fixtures support software tests only and are not evidence of real-world performance.

## Next evidence required

Before predictive modeling or operational use, define a target from an independent and defensible source, document spatial/temporal alignment, check label quality, compare with a simple baseline, and evaluate on a later held-out period. For local water decisions, involve domain expertise and account for crop, soil, irrigation, seasonality, groundwater, and other omitted factors.
