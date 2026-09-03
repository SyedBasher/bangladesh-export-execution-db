# BEOED v0.1.2 Screening-Semantics Patch

This patch follows the successful v0.1.1 QA build. It addresses issues revealed by substantive inspection rather than build failures.

## Why another revision was necessary

The v0.1.1 pipeline passed all formal QA checks, but the top public sample still placed very large foreign markets such as passenger vehicles and raw commodities near the top because `market_attractiveness` was intentionally a market-side measure. A secondary sort on product-space density was not enough to prevent a reader from misreading the sample as an opportunity ranking.

## Main changes

1. `readiness_index` is renamed `trade_familiarity_index`. Export history and destination familiarity are useful evidence, but they do not prove technical readiness.
2. Five-year growth from a base below USD 1 million receives a neutral contribution to the attractiveness index. Raw CAGR remains visible together with `market_growth_status`.
3. Public v0.2 adds transparent capability classes rather than a black-box opportunity score:
   - `established_rca`
   - `emerging_observed`
   - `adjacent_observed`
   - `latent_adjacent`
   - `distant_or_unobserved`
4. Product-space adjacency is split between manufacturing and resource/endowment-dependent products. `latent_adjacent` always means *requires feasibility validation*.
5. `screening_class` distinguishes established-product market gaps, emerging-product market gaps, adjacent manufacturing cases requiring validation, existing strong positions, resource/endowment cases requiring validation, and exploratory rows.
6. The private model receives absolute product/destination trade-scale features in addition to percentile experience measures.
7. `survival_probability_3y` becomes `persistence_probability_3y`; `execution_probability` becomes `durable_entry_score` to avoid false fixed-horizon probability semantics.
8. QA enforces minimum predictive performance and reports classification counts and missing-ISO destinations.

## Deployment

Copy the contents of this patch into the repository root, overwrite matching files, commit, push, let `Test BEOED` pass, then run `Full BEOED build` again.

Do not publish the database yet. After the build, inspect `qa_report.json`, `validation_report.json`, `release_manifest.json`, and the three class-specific public sample CSVs.
