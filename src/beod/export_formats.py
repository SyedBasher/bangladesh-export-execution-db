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

V02_PUBLIC_EXTRA = [
    "pci","pci_rank","pci_percentile","density_bd","density_bd_percentile",
    "rca_bd","bd_rca1","world_exports_usd","product_space_status"
]


def _stata_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a Stata-safe copy while preserving analytical numeric values."""
    out = df.copy()
    if "hs6" in out.columns:
        out["hs6"] = out["hs6"].astype("string").fillna("").str.zfill(6).astype(str)
    for col in out.columns:
        if col == "hs6":
            continue
        if pd.api.types.is_object_dtype(out[col].dtype) or pd.api.types.is_string_dtype(out[col].dtype):
            out[col] = out[col].astype("string").fillna("").astype(str)
    return out


def _write_stata_optional(df: pd.DataFrame, path: Path):
    try:
        _stata_safe(df).to_stata(path, write_index=False, version=118)
    except (ValueError, TypeError, NotImplementedError) as exc:
        warnings.warn(
            f"Stata export skipped because pandas.to_stata rejected a column: {exc}. "
            "Parquet/CSV outputs remain canonical.",
            RuntimeWarning,
        )


def export_public(snapshot: pd.DataFrame, out_dir: Path, sample_rows: int = 5000):
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [c for c in PUBLIC_COLS if c in snapshot.columns]
    pub = snapshot[cols].copy()
    pub.to_parquet(out_dir / "beoed_public_latest.parquet", index=False, compression="zstd")
    pub.to_csv(out_dir / "beoed_public_latest.csv.gz", index=False, compression="gzip")
    sample = pub.sort_values(["market_attractiveness","readiness_index"], ascending=False).head(sample_rows)
    sample.to_csv(out_dir / "beoed_public_sample.csv", index=False)
    _write_stata_optional(pub, out_dir / "beoed_public_latest.dta")


def export_public_v02(snapshot_v02: pd.DataFrame, out_dir: Path, sample_rows: int = 5000):
    """Public transparent screening layer: no private model probabilities."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [c for c in PUBLIC_COLS + V02_PUBLIC_EXTRA if c in snapshot_v02.columns]
    pub = snapshot_v02[cols].copy()
    pub.to_parquet(out_dir / "beoed_public_screening_v02.parquet", index=False, compression="zstd")
    pub.to_csv(out_dir / "beoed_public_screening_v02.csv.gz", index=False, compression="gzip")
    sample = pub.sort_values(
        ["market_attractiveness","density_bd_percentile","readiness_index"],
        ascending=False,
        na_position="last",
    ).head(sample_rows)
    sample.to_csv(out_dir / "beoed_public_screening_v02_sample.csv", index=False)
    _write_stata_optional(pub, out_dir / "beoed_public_screening_v02.dta")


def build_duckdb(data_dir: Path, db_path: Path):
    """Build a portable DuckDB containing physical tables, not external-path views."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    p1 = str(data_dir / "beoed_public_latest.parquet").replace("'", "''")
    con.execute(f"CREATE TABLE public_latest AS SELECT * FROM read_parquet('{p1}')")
    p2 = data_dir / "beoed_public_screening_v02.parquet"
    if p2.exists():
        qp2 = str(p2).replace("'", "''")
        con.execute(f"CREATE TABLE public_screening_v02 AS SELECT * FROM read_parquet('{qp2}')")
    con.close()
