# Build status

## Current stage: QA / pre-release

A full BACI 202601 HS2012 build completed successfully on GitHub Actions on 3 September 2026. The first artifact exposed several issues before public release: missing ISO3 metadata, mojibake in some country names, duplicated-entity weighting in percentile features, a non-portable DuckDB view, and post-entry feature timing in the persistence model.

The v0.1.1 QA revision addresses those issues and adds a hard release gate. The database should remain labelled **pre-release** until a new full build returns `qa_pass: true` and model diagnostics have been reviewed.

### Required before first public data release
- full GitHub build passes unit tests and `scripts/run_qa.py`;
- `models/qa_report.json` has no critical failures;
- ISO3/name coverage and text encoding pass;
- DuckDB is self-contained;
- v0.2 RCA/PCI/density fields merge with high coverage;
- entry/persistence rolling holdout metrics are reviewed;
- selected HS6-destination observations are manually cross-checked against BACI/partner data;
- exact ECI/PCI ranks are benchmarked against an independent implementation before being highlighted publicly.
