# GitHub distribution architecture

## Public repository / GitHub Pages

Use the repository for documentation, the public build pipeline, the codebook, Stata examples, a small sample, and release notes. The Pages site should explain the data product and link to versioned data assets.

Do **not** commit the complete Parquet/DuckDB release if it exceeds ordinary repository limits. Attach large versioned files to GitHub Releases instead.

Suggested navigation:

1. Overview
2. Download latest public research edition
3. User guide
4. Methodology
5. Data dictionary
6. Interpretation and cautions
7. Release history
8. Bespoke research / contact

## Internal repository

Keep model fitting code, model artifacts, entry/persistence scores, diagnostic rules that are commercially sensitive, firm-capability matches, and client-specific data in a separate private repository or private storage.

The public repository should demonstrate reproducibility of the descriptive layer without publishing the entire commercial execution layer.
