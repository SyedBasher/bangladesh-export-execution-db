from __future__ import annotations
import numpy as np
import pandas as pd


def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average").clip(0, 1)


def safe_cagr(v0: pd.Series, v1: pd.Series, years: int) -> pd.Series:
    out = pd.Series(np.nan, index=v1.index, dtype=float)
    ok = (v0 > 0) & (v1 >= 0)
    out.loc[ok] = (v1.loc[ok] / v0.loc[ok]) ** (1 / years) - 1
    return out


def add_transparent_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Descriptive public indices. These are intentionally simple and auditable."""
    out = df.copy()
    log_market = np.log1p(out["destination_market_usd"].clip(lower=0))
    out["market_size_pct"] = pct_rank(log_market)
    out["market_growth_pct"] = pct_rank(out["market_cagr_5y"].fillna(out["market_cagr_5y"].median()))
    out["supplier_openness_pct"] = pct_rank((1 - out["supplier_hhi"]).clip(0, 1))
    out["market_attractiveness"] = 100 * (
        0.50 * out["market_size_pct"]
        + 0.30 * out["market_growth_pct"]
        + 0.20 * out["supplier_openness_pct"]
    )
    out["readiness_index"] = 100 * (
        0.60 * out["product_experience"] + 0.40 * out["destination_familiarity"]
    )
    return out


def diagnostic_flags(row: pd.Series) -> str:
    flags = []
    if pd.notna(row.get("market_cagr_5y")) and row["market_cagr_5y"] < 0:
        flags.append("declining_market")
    if row.get("top_supplier_share", 0) >= 0.60:
        flags.append("high_supplier_concentration")
    if row.get("destination_familiarity", 1) < 0.25:
        flags.append("low_destination_familiarity")
    if row.get("product_experience", 1) < 0.25:
        flags.append("low_product_experience")
    if row.get("bd_market_share", 0) >= 0.20:
        flags.append("already_high_share")
    return ";".join(flags) if flags else "none"
