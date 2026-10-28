# Day 9 — Independent Reference Target & Forecasting Readiness

## Purpose

AQUA-SENSE needs evidence that is not just a restatement of signals used by its index. Day 9 introduces a contract for reference observations and a registry of candidate data sources. It does not claim that a real-world target series has already been collected or validated.

## Candidate reference signals

### 1. NASA SMAP surface soil moisture — component-level comparison

NASA's SMAP data products provide satellite-derived soil-moisture estimates. A daily enhanced Level-3 product is described at approximately 9 km resolution, and product version and quality flags matter for actual extraction. See the [NASA global soil moisture data page](https://earth.gsfc.nasa.gov/hydro/data/nasa-usda-global-soil-moisture-data) and the [NASA SMAP product catalogue](https://data.nasa.gov/dataset/smap-l3-radiometer-global-daily-36-km-ease-grid-soil-moisture-v009).

Use it to test whether the Open-Meteo soil-moisture signal has plausible temporal direction and regional agreement after checking the exact product, quality flags, grid cell, land cover, and time window.

Do not use it alone as independent ground truth for the composite stress index: the index already includes soil moisture. A different provider makes the source distinct but does not remove overlap in the physical construct. Treat this as component-level reference evidence.

### 2. Central Ground Water Board observations — hydrological context

The [CGWB monitoring page](https://cgwb.gov.in/en/ground-water-level-monitoring) describes a national monitoring network, periodic measurements, and some telemetry-enabled higher-frequency stations. The [National Water Data Portal telemetry dataset](https://www.nwdp.nwic.gov.in/dataset/ground-water-level-telemetry-hourly-central-ground-water-board-cgwb) is one possible starting point; station coverage, access terms, and cadence need to be checked.

Groundwater depth is an independent hydrological variable relative to the current four index inputs. It may support a separately defined groundwater-stress task, but is not automatically a direct label for daily surface-soil or crop stress. Well depth, measurement date, station location, aquifer context, and intended outcome must align.

### 3. Official drought classification — possible outcome target

The [India Manual for Drought Management](https://vedas.sac.gov.in/static/pdf/Drought%20Manual-2020.pdf) discusses drought assessment across rainfall, vegetation, water, crop, and other indicator groups. A documented official assessment may be a more directly interpretable outcome for an administrative-area/season classification task, provided a consistent machine-readable series can be sourced.

Before using this target, confirm the classification source, methodology, date range, geographic unit, revision history, and independence from chosen model inputs. This repository does not yet contain an official drought label series.

### 4. Local field observations — highest contextual value, with collection effort

Locally measured or reviewed field water-stress observations may have strong relevance to the intended decision. They require an agreed protocol, clearly described categories, sampling dates and plot locations, trained assessors, quality checks, and appropriate permission. Anecdotal or retrospectively assigned labels should not be treated as gold-standard evidence.

## Target data contract

The schema in data/schemas/reference-target.schema.json defines required fields for source identity, timezone-aware timestamp, location, target variable/value/unit, temporal and spatial support, quality flag, and independence assessment.

The validator in src/validation/reference_target.py checks:
- known target variables and matching units;
- finite numeric values and range checks where applicable;
- categorical labels that preserve source categories;
- timezone-aware timestamps;
- grid-cell spatial resolution;
- reviewer and review timestamp when a record is marked approved;
- basic source independence and target-construct overlap against declared model inputs.

The mechanical independence screen is deliberately modest. It does not prove scientific validity, prevent all forms of leakage, or replace human review. An approved status should only be assigned after documenting the decision, reviewer, and review timestamp.

## Candidate target registry

The registry in config/reference_target_registry.json records candidate sources and appropriate usage limits. These are discovery candidates only: data have not been downloaded, spatially joined, temporally aligned, or validated as targets by this commit.

## Evaluation gate before model training

1. Pick one prediction task and define its target and forecast horizon precisely.
2. Find a real source series and inspect coverage, units, revisions, quality flags, and license/access restrictions.
3. Verify source independence and assess construct overlap with features.
4. Align temporal and spatial support without forward-filling future information.
5. Freeze the labeling rules and preserve provenance.
6. Use time-aware training/validation/test partitions and keep a later period held out.
7. Compare against a simple baseline and report results only after the target is actually available.

Until those conditions are met, AQUA-SENSE reports can describe index sensitivity, but must not claim validated predictive accuracy.
