# BEOED v0.1.1 QA revision patch

Copy the **contents of this folder** into the root of `bangladesh-export-execution-db`, allowing Windows to replace files with the same names. The patch deliberately does not include `docs/index.html`, website CSS/JS, or seed firm data, so the current GitHub Pages site is not overwritten.

## Corrections
1. BACI `country_iso3` is recognized and ISO3 codes are validated.
2. Common mojibake such as `TÃ¼rkiye` is repaired conservatively.
3. Product/destination percentile features are ranked over unique products/destinations rather than repeated product-market rows.
4. Survival predictors move to the pre-entry year `y-1`.
5. DuckDB uses physical tables and is portable without adjacent Parquet files.
6. SQL aliases from the live CI fixes are retained.
7. Stata export remains optional and cannot invalidate canonical Parquet/CSV outputs.

## Analytical revisions
- rolling out-of-time validation;
- PR-AUC, Brier baseline/skill, top-5% lift/capture, calibration intercept/slope and ECE;
- public v0.2 screening dataset exposing RCA/PCI/product-space components separately;
- no combined public "opportunity score";
- automated QA gate covering keys, metadata, encoding, arithmetic, bounds, v0.2 coverage and DuckDB portability;
- richer release manifest.

## After copying
1. Commit: `Apply BEOED v0.1.1 QA revision`
2. Push to GitHub.
3. Wait for `Test BEOED` to pass.
4. Run `Full BEOED build` manually.
5. Download/upload `models/qa_report.json`, `models/validation_report.json`, `release_manifest.json`, and (if QA passes) `data/public/beoed_public_screening_v02_sample.csv` for review.

Do not publish a formal release until `qa_pass` is true and model diagnostics have been reviewed.
