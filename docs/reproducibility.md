# Reproducibility

## Build

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_all.py
```

The pipeline downloads the pinned CEPII BACI archive, processes one annual file at a time, writes compact ZSTD Parquet aggregates, creates the latest product-market snapshot, and exports public Parquet/CSV/Stata/DuckDB files.

## Why Python is the production language

Python/DuckDB can stream and aggregate files that exceed spreadsheet limits, automate releases, estimate models, and generate Stata/CSV/Parquet outputs from one source of truth. Stata is supported as a consumption/analysis format through `.dta` releases and example `.do` files.

## Vintages

Do not silently overwrite historical releases. Every release should record BACI version, HS revision, build date, code commit and model specification. Material revisions should receive a new semantic version and changelog entry.
