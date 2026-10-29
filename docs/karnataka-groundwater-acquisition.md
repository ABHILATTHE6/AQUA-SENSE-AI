# Day 10 — Karnataka Groundwater Reference Acquisition & Quality Review

## Dataset selection

The initial reference candidate is the public telemetry CSV exposed by the National Water Data Portal for the Karnataka Ground Water Department (the portal labels the provider Karnataka GW). The dataset description says it contains station, geographic hierarchy, timestamp, and groundwater-level measurements in metres. The specific resource is the six-hourly Karnataka export covering 2021–2025.

- Dataset page: https://nwdp.nwic.gov.in/en/dataset/ground-water-level-telemetry-hourly-karnataka-ground-water-department
- CSV resource: https://nwdp.nwic.gov.in/dataset/832fa98a-93d2-4f5b-8c4a-28964b4993db/resource/f6178453-cbc0-4005-98b3-8408e6dfc19a/download/gwl_tel_6_hourly_karnataka_gw_ka_2021_2025.csv
- Portal resource metadata reports CSV format and an open licence category. Verify the portal's current terms and metadata before redistribution or publication.

This is **Karnataka Ground Water Department data**, not a CGWB-owned station file. It is registered under its own source ID to avoid misattributing the producer. Groundwater depth can support a separately defined groundwater-stress task or provide hydrological context; it is not automatically a daily crop-water-stress label.

## Run acquisition and profiling

From the repository root, use:

    python scripts/ingest_karnataka_groundwater.py

The default command downloads the CSV to a dated, Git-ignored raw-data partition, preserves source bytes, computes a SHA-256 checksum, normalizes valid observations to JSONL, quarantines invalid rows, and writes a quality report. The download is streamed and has a default 2 GiB size cap.

For a first-pass processing check after downloading, use:

    python scripts/ingest_karnataka_groundwater.py --input data/raw/karnataka_groundwater/YYYY-MM-DD/karnataka_gwl_2021_2025.csv --limit 1000

Local-input mode skips network access but still writes normalized records, rejected rows, and the report. The limit applies to rows processed, not bytes downloaded. The default report and output paths can be changed using --report, --output, --rejects, and --raw-output.

## Normalization contract

Valid rows are transformed into the existing reference-target schema:

- source ID: karnataka_groundwater;
- target: groundwater_depth_m, in metres;
- temporal support: instantaneous measurement at the recorded acquisition time;
- spatial support: station point, with station/district and optional coordinates retained in metadata;
- independence status: candidate, never automatically approved.

A timestamp that already includes an offset keeps that offset. A naive timestamp is interpreted using the configurable source timezone, default Asia/Kolkata. Confirm this assumption against source documentation before scientific analysis. Original timestamp text and timezone assumption are retained in every output record.

## Quality checks and outputs

The report includes input, accepted and rejected row counts; rejection reasons; duplicate station/timestamp observations; unique station locations and districts; time coverage; coordinate completeness; and minimum/maximum non-negative groundwater depth. Rejected records are preserved in a separate JSONL quarantine file with row number and reason. Missing values are not filled and outliers are not auto-corrected.

The parser accepts common header variations for station, timestamp, and groundwater depth while failing fast if required fields cannot be identified. Invalid timestamps, missing station names, nonnumeric or nonfinite measurements, negative depth values, and duplicate station/timestamp records do not enter the normalized output.

## Interpretation and limits

This dataset is a **candidate hydrological reference**, not approved ground truth. Before joining it with weather or the water-stress index, review station coordinates, units and datum, time zone, sampling cadence, missingness, duplicate behavior, and station coverage. A groundwater measurement may not match the temporal or physical scale of surface soil moisture or crop stress.

The connector has deterministic fixture tests. A real data download and quality summary must be generated in an environment that can reach the portal; no downloaded source CSV is stored in Git. The report explicitly leaves predictive accuracy unassessed.
