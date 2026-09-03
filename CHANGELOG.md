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

## v0.1.2 — screening semantics and model robustness
- Renamed the public `readiness_index` to `trade_familiarity_index`; observed trade history is not technical readiness.
- Added absolute Bangladesh product export scale/breadth to the public descriptive layer and private predictive feature set.
- Five-year growth from a historical market base below USD 1 million no longer receives an artificially high growth contribution in `market_attractiveness`; it is flagged as `small_base` or `missing_base`.
- Added transparent v0.2 `product_group`, `capability_status`, `market_condition`, `screening_class`, and `complexity_upgrade_flag` fields. Latent product-space adjacency is explicitly labelled as requiring feasibility validation.
- Replaced `survival_probability_3y` with `persistence_probability_3y` because the outcome is activity at y+3, not continuous annual survival.
- Replaced `execution_probability` with `durable_entry_score`; the product of entry and persistence probabilities is a composite ranking score, not a single fixed-horizon calibrated probability.
- QA now reports missing-ISO destinations, screening-class/capability counts, v0.2 DuckDB portability, and minimum predictive-performance checks.
- Public v0.2 examples are balanced across screening classes; dedicated example extracts are produced for established-product market gaps, emerging products, and adjacent manufacturing cases.
