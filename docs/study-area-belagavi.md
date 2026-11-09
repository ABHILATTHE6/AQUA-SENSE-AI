# Day 12 — Belagavi Pilot Study Area & Local-Time Weather Acquisition

## Pilot selection

The first Karnataka pilot is Belagavi city. The configured reference coordinate is 15.8521° N, 74.5045° E, taken from the Belagavi Cantonment Board city-map reference. It is a representative city coordinate for requesting gridded historical weather; it is not the location of a specific groundwater well, a rain gauge, or an identified weather-grid cell centre.

Official coordinate reference: https://belgaum.cantt.gov.in/city-map/

The location is stored in config/locations.json and its study-area assumptions are recorded separately in config/study_areas.json. The neutral demo location remains available and has not been repurposed.

## Weather source and model

The selected source is the Open-Meteo Historical Weather API. The current AQUA-SENSE input contract needs hourly precipitation, temperature, relative humidity, ET₀ and 0–7 cm soil moisture. ERA5 is chosen for this first consistent extraction because the Open-Meteo model comparison lists these inputs across the ERA5 dataset; ERA5 is a coarser 0.25° grid (about 25 km). ERA5-Land is finer at 0.1° (about 11 km), but the published variable availability table does not list precipitation for ERA5-Land. Mixing a precipitation series from a different model in this first run would make the source/model assumptions less consistent.

Open-Meteo describes these historical values as reanalysis estimates and documents the model resolutions, variables and timezone options. They are not direct observations from a Belagavi weather station. See the [Historical Weather API documentation](https://open-meteo.com/en/docs/historical-weather-api).

## Local timezone and timestamp correction

Belagavi uses Asia/Kolkata. The historical API supports IANA timezone names and returns time information according to the selected timezone. Its documentation notes that DST changes during a requested range are ignored; India has no seasonal DST shift. Day 12 updates normalization so a timestamp with no explicit offset is interpreted in the provider timezone rather than incorrectly being tagged as UTC.

The raw payload remains unchanged in the raw layer. Normalized hourly records retain the requested/provider timezone and UTC offset metadata. Daily grouping converts aware timestamps into Asia/Kolkata before applying calendar boundaries. This avoids assigning an early-morning Belagavi observation to the previous UTC date.

## Run the preflight and acquire a first year

From the repository root:

    python scripts/check_study_area_readiness.py --study-area belagavi_city_pilot

Acquire one complete 2025 calendar year as the first reproducible weather window:

    python scripts/ingest_historical_weather.py --location belagavi_city_pilot --start-date 2025-01-01 --end-date 2025-12-31

The command uses the location's saved coordinates, timezone and model, preserving the raw API response and writing hourly and local-day JSONL under data/processed/belagavi_city_pilot/. The 366-day request limit remains in force. A full-year run is a first acquisition window, not proof of complete or valid groundwater alignment.

Run the station proximity audit after Day 10 groundwater ingestion:

    python scripts/check_study_area_readiness.py --study-area belagavi_city_pilot --groundwater-input data/processed/reference/karnataka_groundwater.jsonl

## Station discovery and join policy

The readiness audit computes distances from the city reference point to groundwater station coordinates. The default 15 km radius only identifies stations for manual inspection; it is not an automatic join threshold. Review the station's physical location, aquifer, measurement reference/datum, timestamp timezone, continuity, and local relevance before choosing one.

The weather request point may be downscaled or mapped to a model grid cell by the provider. Keep the returned latitude/longitude and model metadata from the raw payload. The API documentation describes a default terrain-aware grid-cell selection process; therefore a distance from a groundwater well to the city request coordinate alone does not prove co-location with the returned grid cell.

No station-to-weather join is performed by this Day 12 pipeline. A later merge must also match local dates, require adequate weather completeness and groundwater-day coverage, and preserve gaps rather than filling them silently.

## Status and limitations

This commit configures the Belagavi pilot and makes the weather ingestion timezone-safe. It adds tests using a synthetic 24-hour provider-shaped payload. It does not claim that a live year of weather has been downloaded or that groundwater stations near Belagavi have been identified. The live weather and groundwater runs must be executed in an environment with network access; their raw data and reports remain outside Git.
