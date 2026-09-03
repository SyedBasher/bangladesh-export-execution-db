from __future__ import annotations
import numpy as np
import pandas as pd


def pct_rank(s: pd.Series) -> pd.Series:
    """Percentile rank on the observations supplied."""
    return s.rank(pct=True, method="average").clip(0, 1)


def safe_cagr(v0: pd.Series, v1: pd.Series, years: int) -> pd.Series:
    out = pd.Series(np.nan, index=v1.index, dtype=float)
    ok = (v0 > 0) & (v1 >= 0)
    out.loc[ok] = (v1.loc[ok] / v0.loc[ok]) ** (1 / years) - 1
    return out


def add_experience_features(
    df: pd.DataFrame,
    product_col: str = "hs6",
    destination_col: str = "destination_code",
    product_exports_col: str = "bd_product_exports_usd",
    product_destinations_col: str = "bd_product_destinations",
    destination_exports_col: str = "bd_destination_exports_usd",
) -> pd.DataFrame:
    """Add product-experience and destination-familiarity measures correctly.

    Product and destination characteristics are constant within product or destination
    in a given cross-section. Ranking the repeated product-market rows would therefore
    overweight products/destinations that happen to appear in more qualifying markets.
    This function ranks the *unique entities* first and merges the scores back.
    """
    out = df.copy()

    d = (
        out[[destination_col, destination_exports_col]]
        .drop_duplicates(destination_col)
        .copy()
    )
    d["destination_familiarity"] = pct_rank(
        np.log1p(pd.to_numeric(d[destination_exports_col], errors="coerce").fillna(0))
    )
    out = out.drop(columns=["destination_familiarity"], errors="ignore").merge(
        d[[destination_col, "destination_familiarity"]],
        on=destination_col,
        how="left",
        validate="many_to_one",
    )

    p = (
        out[[product_col, product_exports_col, product_destinations_col]]
        .drop_duplicates(product_col)
        .copy()
    )
    p["product_scale_pct"] = pct_rank(
        np.log1p(pd.to_numeric(p[product_exports_col], errors="coerce").fillna(0))
    )
    p["product_breadth_pct"] = pct_rank(
        pd.to_numeric(p[product_destinations_col], errors="coerce").fillna(0)
    )
    p["product_experience"] = (
        0.75 * p["product_scale_pct"] + 0.25 * p["product_breadth_pct"]
    ).clip(0, 1)
    out = out.drop(
        columns=["product_scale_pct", "product_breadth_pct", "product_experience"],
        errors="ignore",
    ).merge(
        p[[product_col, "product_scale_pct", "product_breadth_pct", "product_experience"]],
        on=product_col,
        how="left",
        validate="many_to_one",
    )
    return out


def add_transparent_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Descriptive public indices. These are intentionally simple and auditable."""
    out = df.copy()
    log_market = np.log1p(out["destination_market_usd"].clip(lower=0))
    out["market_size_pct"] = pct_rank(log_market)
    growth = out["market_cagr_5y"]
    fallback = growth.median() if growth.notna().any() else 0.0
    out["market_growth_pct"] = pct_rank(growth.fillna(fallback))
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
    if row.get("bd_exports_to_destination_usd", 0) == 0:
        flags.append("no_current_bd_exports")
    return ";".join(flags) if flags else "none"
