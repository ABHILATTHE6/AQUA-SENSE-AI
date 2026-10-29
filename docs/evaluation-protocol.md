# Day 8 — Baseline Evaluation & Time-Aware Comparison

## Goal

Day 8 creates a reproducible protocol for inspecting the initial rule-based water-stress index. The aim is to measure reproducibility and sensitivity to transparent assumptions, not to overstate what the index proves.

## Sensitivity is not accuracy

The current index is a deterministic function of daily rainfall, near-surface soil moisture, ET0, and mean temperature. The project does not yet contain an independent, trusted target label for water stress or drought. Therefore the workflow reports no predictive accuracy, precision, recall, R-squared, MAE, or RMSE. Those metrics would be unjustified without a reference target and a defined prediction horizon.

## Configurations

The report uses five explicit scenarios:

1. baseline_v1: current default thresholds and weights;
2. equal_weights: every component receives weight 0.25;
3. soil_moisture_emphasis: soil moisture receives weight 0.50;
4. atmospheric_demand_emphasis: greater combined weight for ET0 and heat;
5. tighter_upper_thresholds: alternative upper normalization thresholds.

For each configuration, the report includes its exact parameters, score distribution, category counts, mean and maximum absolute score shift from the default, and the proportion of rows changing category. These are descriptive sensitivity measures. The alternatives are not fitted to the dataset.

## Time-aware partitions

The chronological splitter divides rows by unique calendar dates into train, validation, and test partitions. The default proportions are 70%, 15%, and 15% by unique date. All locations on one calendar date remain in the same partition, and duplicate date/location observations are rejected. No random shuffling occurs. At least three unique dates are required.

In this Day 8 report, temporal partitions describe how scores and sensitivity vary across earlier, middle, and later periods only. They are not model training or held-out predictive evaluation results. If the input is too short, whole-dataset sensitivity is still reported and the time analysis is explicitly marked unavailable.

## Run the report

    python scripts/evaluate_water_stress_baseline.py --input <daily.jsonl> --output reports/water_stress_sensitivity.json

Input JSONL rows must contain the fields used by the baseline scorer: date, rainfall_mm_sum, soil_moisture_m3_m3_mean, et0_mm_sum, and air_temperature_c_mean. A location_id is used for unique observation identity and comparison alignment.

## Interpretation guide

- A large mean score shift suggests the score depends meaningfully on the tested weight/threshold assumptions.
- A high category-change rate suggests provisional category labels are unstable under the tested alternatives.
- Low sensitivity across these few scenarios does not prove that the thresholds are scientifically valid.
- Period differences can reflect seasonality, incomplete coverage, or data quality; they do not establish model degradation.
- Synthetic fixtures test software behavior only and are not evidence of real-world performance.

## Evidence required next

Before predictive modeling or operational use, define a target from an independent and defensible source, document spatial and temporal alignment, check label quality, compare with a simple baseline, and evaluate on a later held-out period. Consult local domain expertise and account for crop, soil, irrigation, seasonality, groundwater, and other currently omitted factors.
