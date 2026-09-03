# BEOED build status — 3 September 2026

## What is actually populated in this package

### v0.3 firm-capability seed
- **28** unique EPB-registered firms.
- **104** observed firm-product registration links.
- Initial coverage: apparel, leather/footwear, jute, bicycles, plastics, pharmaceuticals, and ceramics.
- Public outputs: CSV and Stata `.dta`.
- Personal names, phone numbers, and emails are deliberately excluded from the public registry.
- Every relationship is tagged as **observed public registry evidence**; no row is presented as proof of capacity, scale, destination, certification, or profitability.

## Production-ready but not populated inside this sandbox

### v0.1 — HS6 x destination trade/execution core
The production pipeline is complete and now includes:
1. BACI 202601 HS2012, 2012–2024 download and streaming aggregation.
2. Bangladesh HS6 x destination history.
3. Destination-product market size and supplier concentration.
4. Bangladesh product experience and destination familiarity.
5. Transparent market-attractiveness and readiness indices.
6. Historical three-year **entry** cohorts.
7. Historical three-year **survival** cohorts.
8. Strict out-of-time validation followed by full-sample refitting.
9. Private `entry_probability_3y`, `survival_probability_3y`, and `execution_probability` fields.
10. Public Parquet, CSV.GZ, Stata, sample CSV, and DuckDB outputs.

The full BACI HS12 archive is about 831 MB. The current ChatGPT sandbox can reach the CEPII webpage but cannot transfer that binary archive. The included GitHub Actions workflow is therefore the intended population route.

### v0.2 — complexity/product-space and market-access enrichment
Implemented from the same BACI latest-year country-product matrix:
- RCA matrix;
- ECI / PCI replication using the normalized country-product matrix;
- Bangladesh product-space density;
- latest-year global product exports;
- optional adapters for HS6 destination tariffs and bilateral gravity/trade-cost variables.

PCI/density are derived research variables. Before external publication they should be cross-checked against an independent implementation; this is part of the release QA gate.

### v0.4 — domestic value capture
The schema and calculation engine are implemented, but no value-capture priors are fabricated in this package. A documented IO/SAM/TiVA mapping must be supplied before v0.4 can run. Initial priors are explicitly sector-level and must never be described as firm-specific.

## Why the public and private layers differ
The public dataset demonstrates provenance, market structure, and transparent descriptive diagnostics. Predictive execution scores, candidate firm matches, constraint diagnostics, and later value-capture/scenario fields remain private or commissioned outputs. This is intentional commercial design, not an omission.
