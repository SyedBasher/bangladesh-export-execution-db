from __future__ import annotations
from pathlib import Path
import warnings
import pandas as pd
import duckdb

PUBLIC_COLS = [
    "year","hs6","product_name","destination_code","destination_name","iso3","destination_market_usd",
    "bd_exports_to_destination_usd","bd_market_share","market_cagr_5y",
    "supplier_hhi","top_supplier_share","destination_familiarity",
    "product_experience","market_attractiveness","readiness_index"
]


def _stata_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a Stata-export-safe copy without changing analytical values.

    pandas.to_stata is stricter than Parquet/CSV about object/string columns:
    nullable pandas strings and all-null object arrays can raise ValueError.
    Missing text values are represented as empty strings in the .dta export.
    """
    out = df.copy()

    # HS codes must remain six-character strings so leading zeroes survive.
    if "hs6" in out.columns:
        out["hs6"] = out["hs6"].astype("string").fillna("").str.zfill(6).astype(str)

    # Convert every text-like column to ordinary Python strings; pandas' Stata
    # writer cannot always handle pd.NA / nullable-string / all-null objects.
    for col in out.columns:
        if col == "hs6":
            continue
        if pd.api.types.is_object_dtype(out[col].dtype) or pd.api.types.is_string_dtype(out[col].dtype):
            out[col] = out[col].astype("string").fillna("").astype(str)

    return out


def export_public(snapshot: pd.DataFrame, out_dir: Path, sample_rows: int = 5000):
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [c for c in PUBLIC_COLS if c in snapshot.columns]
    pub = snapshot[cols].copy()

    # Master public formats. These should be written regardless of Stata support.
    pub.to_parquet(out_dir / "beoed_public_latest.parquet", index=False, compression="zstd")
    pub.to_csv(out_dir / "beoed_public_latest.csv.gz", index=False, compression="gzip")

    sample = pub.sort_values(["market_attractiveness", "readiness_index"], ascending=False).head(sample_rows)
    sample.to_csv(out_dir / "beoed_public_sample.csv", index=False)

    # Stata is an analyst convenience format, not the canonical master format.
    # Sanitize nullable strings so a format-specific issue does not invalidate
    # an otherwise successful Parquet/CSV build.
    stata = _stata_safe(pub)
    try:
        stata.to_stata(out_dir / "beoed_public_latest.dta", write_index=False, version=118)
    except (ValueError, TypeError) as exc:
        warnings.warn(
            f"Stata export skipped because pandas.to_stata rejected a column: {exc}. "
            "Parquet and CSV outputs were written successfully.",
            RuntimeWarning,
        )


def build_duckdb(data_dir: Path, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    pq = str(data_dir / "beoed_public_latest.parquet").replace("'", "''")
    con.execute(f"CREATE OR REPLACE VIEW public_latest AS SELECT * FROM read_parquet('{pq}')")
    con.close()
