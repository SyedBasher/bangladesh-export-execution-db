# Changelog

## v0.1.1 — QA revision (2026-09-03)
- Recognize BACI `country_iso3` metadata and validate ISO3 format.
- Repair common mojibake in metadata labels.
- Compute product/destination percentile features over unique entities, avoiding repeated-row weighting.
- Move survival-model predictors to the pre-entry year.
- Add PR-AUC, Brier skill, top-5% lift/capture and calibration diagnostics.
- Add rolling out-of-time model validation.
- Make DuckDB release self-contained with physical tables.
- Add transparent public v0.2 screening output with RCA/PCI/density components.
- Add automated release QA gate and richer release manifest.

## v0.1.0 — initial build
- BACI 202601 HS2012 trade backbone and public screening snapshot.
- Baseline entry/survival model architecture.
- Internal product-space layer.
- EPB firm-capability seed registry.
