from __future__ import annotations
import numpy as np
import pandas as pd

# Five-year growth rates can become economically meaningless when the base market is
# extremely small. BEOED still reports the raw CAGR, but the public attractiveness
# index treats sub-threshold bases as neutral rather than rewarding explosive growth
# from a de minimis starting point.
DEFAULT_GROWTH_BASE_MIN_USD = 1_000_000.0


def pct_rank(s: pd.Series) -> pd.Series:
    """Percentile rank on the observations supplied."""
    return s.rank(pct=True, method="average").clip(0, 1)


def safe_cagr(v0: pd.Series, v1: pd.Series, years: int) -> pd.Series:
    out = pd.Series(np.nan, index=v1.index, dtype=float)
    ok = (v0 > 0) & (v1 >= 0)
    out.loc[ok] = (v1.loc[ok] / v0.loc[ok]) ** (1 / years) - 1
    return out


def reliable_growth_for_model(
    v0: pd.Series,
    v1: pd.Series,
    years: int,
    min_base_usd: float = DEFAULT_GROWTH_BASE_MIN_USD,
) -> pd.Series:
    """Return CAGR only where the historical market base is economically meaningful."""
    g = safe_cagr(v0, v1, years)
    return g.where(pd.to_numeric(v0, errors="coerce") >= float(min_base_usd))


def add_experience_features(
    df: pd.DataFrame,
    product_col: str = "hs6",
    destination_col: str = "destination_code",
    product_exports_col: str = "bd_product_exports_usd",
    product_destinations_col: str = "bd_product_destinations",
    destination_exports_col: str = "bd_destination_exports_usd",
) -> pd.DataFrame:
    """Add transparent Bangladesh product/destination experience measures.

    Product and destination characteristics are constant within product or destination
    in a given cross-section. Ranking repeated product-market rows would overweight
    products/destinations that happen to appear in more qualifying markets. We therefore
    rank unique entities first and merge those scores back.

    These are *trade familiarity* measures, not proof of production capability.
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


def add_absolute_model_features(
    df: pd.DataFrame,
    product_exports_col: str = "bd_product_exports_usd",
    product_destinations_col: str = "bd_product_destinations",
    destination_exports_col: str = "bd_destination_exports_usd",
) -> pd.DataFrame:
    """Add absolute-scale features used only by the private predictive layer."""
    out = df.copy()
    out["log_product_exports_usd"] = np.log1p(
        pd.to_numeric(out[product_exports_col], errors="coerce").fillna(0).clip(lower=0)
    )
    out["log_destination_exports_usd"] = np.log1p(
        pd.to_numeric(out[destination_exports_col], errors="coerce").fillna(0).clip(lower=0)
    )
    out["log_product_destinations"] = np.log1p(
        pd.to_numeric(out[product_destinations_col], errors="coerce").fillna(0).clip(lower=0)
    )
    return out


def add_transparent_indices(
    df: pd.DataFrame,
    *,
    base_col: str = "market_base_usd_5y",
    growth_base_min_usd: float = DEFAULT_GROWTH_BASE_MIN_USD,
) -> pd.DataFrame:
    """Add descriptive public indices with explicit limits.

    ``market_attractiveness`` summarizes market size, *reliably measured* five-year
    growth, and supplier openness. If a five-year base is absent or below the configured
    threshold, growth receives a neutral percentile rather than a top score.

    ``trade_familiarity_index`` summarizes Bangladesh's observed product export history
    and destination relationship. It deliberately avoids the word ``readiness`` because
    trade history alone does not establish technical or firm-level capability.
    """
    out = df.copy()
    log_market = np.log1p(pd.to_numeric(out["destination_market_usd"], errors="coerce").clip(lower=0))
    out["market_size_pct"] = pct_rank(log_market)

    growth = pd.to_numeric(out["market_cagr_5y"], errors="coerce")
    if base_col in out.columns:
        base = pd.to_numeric(out[base_col], errors="coerce")
        stable = base >= float(growth_base_min_usd)
        out["market_growth_status"] = np.select(
            [stable, base.gt(0) & ~stable],
            ["stable_base", "small_base"],
            default="missing_base",
        )
        ranked_growth = pct_rank(growth.where(stable))
        out["market_growth_pct"] = ranked_growth.fillna(0.5)
    else:
        out["market_growth_status"] = "base_not_supplied"
        fallback = growth.median() if growth.notna().any() else 0.0
        out["market_growth_pct"] = pct_rank(growth.fillna(fallback))

    out["supplier_openness_pct"] = pct_rank(
        (1 - pd.to_numeric(out["supplier_hhi"], errors="coerce")).clip(0, 1)
    )
    out["market_attractiveness"] = 100 * (
        0.50 * out["market_size_pct"]
        + 0.30 * out["market_growth_pct"]
        + 0.20 * out["supplier_openness_pct"]
    )
    out["trade_familiarity_index"] = 100 * (
        0.60 * out["product_experience"] + 0.40 * out["destination_familiarity"]
    )
    return out


def diagnostic_flags(row: pd.Series) -> str:
    flags = []
    if pd.notna(row.get("market_cagr_5y")) and row["market_cagr_5y"] < 0:
        flags.append("declining_market")
    if row.get("market_growth_status") in {"small_base", "missing_base"}:
        flags.append("growth_base_unreliable")
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
