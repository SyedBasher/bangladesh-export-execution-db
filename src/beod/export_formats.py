from __future__ import annotations
from pathlib import Path
import pandas as pd
import duckdb

PUBLIC_COLS = [
    "year","hs6","product_name","destination_code","destination_name","iso3","destination_market_usd",
    "bd_exports_to_destination_usd","bd_market_share","market_cagr_5y",
    "supplier_hhi","top_supplier_share","destination_familiarity",
    "product_experience","market_attractiveness","readiness_index"
]


def export_public(snapshot: pd.DataFrame, out_dir: Path, sample_rows: int = 5000):
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [c for c in PUBLIC_COLS if c in snapshot.columns]
    pub = snapshot[cols].copy()
    pub.to_parquet(out_dir / "beoed_public_latest.parquet", index=False, compression="zstd")
    pub.to_csv(out_dir / "beoed_public_latest.csv.gz", index=False, compression="gzip")
    sample = pub.sort_values(["market_attractiveness","readiness_index"], ascending=False).head(sample_rows)
    sample.to_csv(out_dir / "beoed_public_sample.csv", index=False)
    # Stata: latest snapshot only; column names are already Stata-safe.
    stata = pub.copy()
    stata["hs6"] = stata["hs6"].astype(str).str.zfill(6)
    stata.to_stata(out_dir / "beoed_public_latest.dta", write_index=False, version=118)


def build_duckdb(data_dir: Path, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    pq = str(data_dir / "beoed_public_latest.parquet").replace("'", "''")
    con.execute(f"CREATE OR REPLACE VIEW public_latest AS SELECT * FROM read_parquet('{pq}')")
    con.close()
