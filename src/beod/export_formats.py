from __future__ import annotations
from pathlib import Path
import warnings
import pandas as pd
import duckdb

from .screening import sample_priority

PUBLIC_COLS = [
    "year","hs6","product_name","destination_code","destination_name","iso3",
    "market_base_usd_5y","destination_market_usd","bd_exports_to_destination_usd",
    "bd_product_exports_usd","bd_product_destinations","bd_product_imports_usd","bd_product_import_origins",
    "bd_product_net_exports_usd","bd_product_log_export_import_ratio","bd_product_positive_years_5y",
    "bd_product_years_ge_100k_5y","bd_product_years_ge_1m_5y","bd_product_exports_5y_mean_usd",
    "bd_product_exports_5y_max_usd","bd_market_share","market_cagr_5y",
    "market_growth_status","supplier_hhi","top_supplier_share","destination_familiarity",
    "product_scale_pct","product_breadth_pct","product_experience","market_attractiveness",
    "trade_familiarity_index"
]

V02_PUBLIC_EXTRA = [
    "pci","pci_rank","pci_percentile","density_bd","density_bd_percentile",
    "rca_bd","bd_rca1","ubiquity_rca1","world_exports_usd","product_space_status",
    "product_group","manufacturing_screen","feasibility_archetype","commercial_screen_exclusion",
    "capability_status","capability_evidence_status","import_dominance_flag","complexity_upgrade_flag",
    "market_condition","screening_class"
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
    sample = pub.sort_values(
        ["market_attractiveness","trade_familiarity_index"], ascending=False
    ).head(sample_rows)
    sample.to_csv(out_dir / "beoed_public_sample.csv", index=False)
    _write_stata_optional(pub, out_dir / "beoed_public_latest.dta")


def _write_class_sample(pub: pd.DataFrame, cls: str, path: Path, n: int = 1000):
    sub = pub.loc[pub["screening_class"].eq(cls)].copy()
    if sub.empty:
        return
    sub = sub.sort_values(
        ["market_attractiveness","complexity_upgrade_flag","density_bd_percentile","trade_familiarity_index"],
        ascending=[False,False,False,False],
        na_position="last",
    ).head(n)
    sub.to_csv(path, index=False)


def export_public_v02(snapshot_v02: pd.DataFrame, out_dir: Path, sample_rows: int = 5000):
    """Public transparent screening layer: no private model probabilities.

    The sample is deliberately balanced across screening classes rather than presented
    as a single opportunity ranking. Separate class-specific extracts are also written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [c for c in PUBLIC_COLS + V02_PUBLIC_EXTRA if c in snapshot_v02.columns]
    pub = snapshot_v02[cols].copy()
    pub.to_parquet(out_dir / "beoed_public_screening_v02.parquet", index=False, compression="zstd")
    pub.to_csv(out_dir / "beoed_public_screening_v02.csv.gz", index=False, compression="gzip")

    temp = pub.copy()
    temp["_priority"] = sample_priority(temp)
    # Avoid letting one large class consume the entire public sample.
    per_class = max(1, sample_rows // max(1, temp["screening_class"].nunique()))
    chunks = []
    for _, g in temp.groupby("screening_class", sort=False):
        g = g.sort_values(
            ["_priority","market_attractiveness","complexity_upgrade_flag","density_bd_percentile","trade_familiarity_index"],
            ascending=[True,False,False,False,False], na_position="last"
        ).head(per_class)
        chunks.append(g)
    sample = pd.concat(chunks, ignore_index=True) if chunks else temp.head(0)
    if len(sample) < sample_rows:
        used = pd.MultiIndex.from_frame(sample[["hs6","destination_code"]])
        all_keys = pd.MultiIndex.from_frame(temp[["hs6","destination_code"]])
        remainder = temp.loc[~all_keys.isin(used)].sort_values(
            ["_priority","market_attractiveness"], ascending=[True,False]
        )
        sample = pd.concat([sample, remainder.head(sample_rows-len(sample))], ignore_index=True)
    sample = sample.drop(columns=["_priority"], errors="ignore").head(sample_rows)
    sample.to_csv(out_dir / "beoed_public_screening_v02_sample.csv", index=False)

    _write_class_sample(pub, "established_product_market_gap", out_dir / "beoed_established_product_market_gaps_sample.csv")
    _write_class_sample(pub, "emerging_product_market_gap", out_dir / "beoed_emerging_products_sample.csv")
    _write_class_sample(pub, "adjacent_downstream_manufacturing_requires_validation", out_dir / "beoed_adjacent_manufacturing_sample.csv")
    _write_class_sample(pub, "recent_export_signal_requires_validation", out_dir / "beoed_recent_export_signals_sample.csv")
    _write_class_sample(pub, "adjacent_process_industry_requires_validation", out_dir / "beoed_process_industry_validation_sample.csv")
    _write_class_sample(pub, "adjacent_advanced_technology_requires_validation", out_dir / "beoed_advanced_technology_validation_sample.csv")

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
