# Day 11 — Groundwater Daily Summaries & Weather Alignment Audit

## Purpose

Day 11 prepares the candidate Karnataka groundwater series for careful comparison with weather. It produces two separate outputs: a local-calendar daily summary per station, and a spatial proximity audit against configured weather locations. It does not produce a merged modeling table.

## Current source context

The National Water Data Portal page lists Karnataka telemetry resources for 2021–2025 and 2026–2030. The 2026–2030 resource page identifies CSV format, an open licence category, and a resource update date of October 23, 2026 at the time checked. Check the live portal metadata and terms before downloading or redistributing.

Dataset page: https://nwdp.nwic.gov.in/dataset/ground-water-level-telemetry-hourly-karnataka-ground-water-department

2026–2030 resource page: https://nwdp.nwic.gov.in/dataset/ground-water-level-telemetry-hourly-karnataka-ground-water-department/resource/97fc90ea-7275-436d-8202-cfcfe089c7f8

## Run the preparation pipeline

After Day 10 acquisition has produced normalized JSONL, run:

    python scripts/prepare_groundwater_alignment.py --input data/processed/reference/karnataka_groundwater.jsonl

The command writes station-day summaries to data/processed/reference/karnataka_groundwater_daily.jsonl and a spatial audit to reports/alignment/karnataka_groundwater_weather_candidates.json. Use --daily-output, --report, and --weather-locations to change output paths.

## Daily summaries

Groundwater records are timezone-aware instantaneous measurements. The pipeline converts each timestamp into the requested named timezone before assigning a calendar day; the default is Asia/Kolkata. For each station and local date, it computes the observed-reading count, coverage against a configurable expected count, mean, median, minimum, maximum, and latest depth.

The default expectation is four readings per day because the portal describes the resource as six-hourly. It is not treated as a strict guarantee: the default minimum for a usable daily comparison is three observations. Every day is retained, but lower-coverage days are marked insufficient. The pipeline does not fill missing observations. It also rejects duplicate station/timestamp pairs and inconsistent station coordinates.

Weather hourly observations must be grouped using the same timezone before any date-based comparison. Existing daily weather records aggregated on UTC calendar dates must not be joined directly to India-local groundwater dates. The daily weather aggregator now accepts a timezone_name parameter for explicit local-day grouping.

## Spatial proximity audit

The station matcher uses station latitude/longitude from groundwater metadata and the configured weather location points in config/locations.json. It calculates great-circle distance with the Haversine formula and reports the nearest three configured points.

A nearest point becomes a candidate only when it is within the configured maximum distance (default 10 km) and is clearly separated from the second-nearest point (default ambiguity margin 1 km). Otherwise it is marked outside radius, ambiguous, or missing coordinates. The thresholds are configurable and are not universal scientific cutoffs.

A candidate point is not an automatic join. The audit does not account for terrain, weather-grid resolution, elevation, basin boundaries, aquifer structure, or local representativeness. A domain review must confirm that the station-weather association is defensible.

## Why no automatic merged dataset?

Groundwater depth measures the water-table position relative to the measurement reference, while weather variables are atmospheric or surface estimates. Their relationship depends on local geology, aquifer properties, pumping, irrigation, recharge, land use, and observation depth. The joined table must remain blocked until station coordinates, timestamps, timezone, target definition, and spatial representativeness have been reviewed.

The current config/locations.json contains a neutral demo coordinate, not a selected Karnataka weather study point. Its spatial audit is expected to report no nearby station candidate for many Karnataka wells. Replace it only after selecting and documenting an actual study area. Do not widen the distance threshold merely to force a match.

## Outputs and limitations

The report shows local-day summary counts, stations and dates represented, sufficient/insufficient day counts, spatial candidate counts by status, configured distance and ambiguity thresholds, and an explicit no-automatic-join flag. The daily series remains candidate hydrological context and is not approved ground truth for the composite water-stress index.

No source CSV or live result is committed to Git. The sample fixture used by tests is synthetic and cannot be interpreted as real groundwater observations.
