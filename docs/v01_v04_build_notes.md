# BEOED v0.1–v0.4 build notes

## v0.1.1 QA revision

This revision corrects five issues identified in the first successful full build:

1. BACI 202601 country metadata uses `country_iso3`; the parser now recognizes it.
2. Common UTF-8/Latin-1 mojibake in country/product labels is repaired conservatively.
3. Product/destination percentile features are ranked across unique entities rather than repeated product-market rows.
4. Survival predictors are measured at `t-1`, before the observed entry at `t`.
5. DuckDB now stores physical tables and remains usable after the source Parquet files are moved.

The model report is expanded to PR-AUC, Brier skill, lift and calibration metrics, with rolling temporal holdouts. A hard QA gate is run before artifacts are accepted.

## v0.1 predictive execution layer

A product-destination entry observation is eligible when Bangladesh is below the configured threshold at year `t`; the outcome is entry in any of `t+1...t+3`. Entry features are observed at `t`.

A survival cohort enters at `t` after being below threshold at `t-1`; outcome is activity at `t+3`. **Survival features are observed at `t-1`.**

## v0.2 product-space layer

The latest BACI country-product matrix is converted to Balassa RCA. The binary `RCA >= 1` matrix is normalized by country diversity and product ubiquity; singular-value decomposition supplies the non-trivial country/product dimensions used for ECI/PCI. Bangladesh density uses standard co-export proximity. Public output exposes components rather than a combined opportunity score.

## v0.3 firm registry

Public EPB records are normalized into one-row-per-firm and one-row-per-observed-product-link tables. The seed remains deliberately incomplete. Candidate matches are labelled `observed_related_hs4`, not `can_produce`.

## v0.4 domestic value capture

Gross export opportunity is not domestic value. v0.4 can attach documented sector priors for domestic value added, imported-input content, labour intensity, energy intensity and financing intensity. Firm-level values require firm data.
