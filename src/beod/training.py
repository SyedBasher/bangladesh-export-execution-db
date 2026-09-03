from __future__ import annotations
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from .features import safe_cagr, add_experience_features


def _add_model_features(df: pd.DataFrame, *, prod_usd: str, prod_dest: str, dest_usd: str) -> pd.DataFrame:
    out = add_experience_features(
        df,
        product_exports_col=prod_usd,
        product_destinations_col=prod_dest,
        destination_exports_col=dest_usd,
    )
    out["log_market_usd"] = np.log1p(out["destination_market_usd"].clip(lower=0))
    return out


def make_transition_panel(agg_dir: Path, years: list[int], entry_usd: float = 100_000) -> pd.DataFrame:
    """Construct pre-entry product-market observations.

    Features are measured at cohort year y. The outcome is whether Bangladesh crosses
    the entry threshold in any of y+1..y+3. No future information enters the features.
    """
    frames = []
    con = duckdb.connect()
    yearset = set(years)
    for y in years:
        if y-5 not in yearset or y+3 not in yearset:
            continue
        yd = agg_dir / f"year={y}"
        y5 = agg_dir / f"year={y-5}"
        future = [agg_dir / f"year={yy}" / "bd_flows.parquet" for yy in range(y+1, y+4)]
        future_union = " UNION ALL ".join([f"SELECT * FROM read_parquet('{p}')" for p in future])
        sql = f"""
          WITH cur AS (
            SELECT m.year,m.hs6,m.destination_code,m.destination_market_usd,m.supplier_hhi,m.top_supplier_share,
                   COALESCE(b.bd_exports_to_destination_usd,0) AS bd_now,
                   COALESCE(p.bd_product_exports_usd,0) AS prod_usd,
                   COALESCE(p.bd_product_destinations,0) AS prod_dest,
                   COALESCE(d.bd_destination_exports_usd,0) AS dest_usd
            FROM read_parquet('{yd/'market_structure.parquet'}') m
            LEFT JOIN read_parquet('{yd/'bd_flows.parquet'}') b USING(year,hs6,destination_code)
            LEFT JOIN read_parquet('{yd/'bd_product.parquet'}') p USING(year,hs6)
            LEFT JOIN read_parquet('{yd/'bd_destination.parquet'}') d USING(year,destination_code)
            WHERE m.destination_market_usd >= 5000000
          ), base AS (
            SELECT hs6,destination_code,destination_market_usd AS market_base
            FROM read_parquet('{y5/'market_structure.parquet'}')
          ), fut AS (
            SELECT hs6,destination_code, MAX(bd_exports_to_destination_usd) AS future_max
            FROM ({future_union}) GROUP BY 1,2
          )
          SELECT cur.*,base.market_base,COALESCE(fut.future_max,0) AS future_max
          FROM cur LEFT JOIN base USING(hs6,destination_code)
          LEFT JOIN fut USING(hs6,destination_code)
          WHERE cur.bd_now < {entry_usd}
        """
        df = con.execute(sql).df()
        if df.empty:
            continue
        df["hs6"] = df["hs6"].astype(str).str.zfill(6)
        df["market_cagr_5y"] = safe_cagr(df["market_base"], df["destination_market_usd"], 5)
        df = _add_model_features(df, prod_usd="prod_usd", prod_dest="prod_dest", dest_usd="dest_usd")
        df["feature_year"] = y
        df["entry_within_3y"] = (df["future_max"] >= entry_usd).astype(int)
        frames.append(df)
    con.close()
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def make_survival_panel(agg_dir: Path, years: list[int], entry_usd: float = 100_000) -> pd.DataFrame:
    """Historical new-entry cohorts and three-year survival outcomes.

    An entry at year y is a relationship below the threshold in y-1 and at/above it
    in y. Crucially, all predictors are measured at y-1, *before entry*. Survival is
    defined as exports at/above the threshold in y+3. This makes the conditional
    persistence model suitable for ex-ante scoring of currently unentered markets.
    """
    frames = []
    con = duckdb.connect()
    yearset = set(years)
    for y in years:
        # Five-year market growth ending at the pre-entry feature year y-1 uses y-6.
        if y-6 not in yearset or y-1 not in yearset or y+3 not in yearset:
            continue
        y_prev = agg_dir / f"year={y-1}"
        y_entry = agg_dir / f"year={y}"
        y_base = agg_dir / f"year={y-6}"
        y3 = agg_dir / f"year={y+3}"
        sql = f"""
        WITH prev AS (
          SELECT m.hs6,m.destination_code,m.destination_market_usd,m.supplier_hhi,m.top_supplier_share,
                 COALESCE(b.bd_exports_to_destination_usd,0) AS bd_prev,
                 COALESCE(p.bd_product_exports_usd,0) AS prod_usd,
                 COALESCE(p.bd_product_destinations,0) AS prod_dest,
                 COALESCE(d.bd_destination_exports_usd,0) AS dest_usd
          FROM read_parquet('{y_prev/'market_structure.parquet'}') m
          LEFT JOIN read_parquet('{y_prev/'bd_flows.parquet'}') b USING(year,hs6,destination_code)
          LEFT JOIN read_parquet('{y_prev/'bd_product.parquet'}') p USING(year,hs6)
          LEFT JOIN read_parquet('{y_prev/'bd_destination.parquet'}') d USING(year,destination_code)
          WHERE m.destination_market_usd >= 5000000
        ), entry AS (
          SELECT hs6,destination_code,bd_exports_to_destination_usd AS bd_entry
          FROM read_parquet('{y_entry/'bd_flows.parquet'}')
        ), base AS (
          SELECT hs6,destination_code,destination_market_usd AS market_base
          FROM read_parquet('{y_base/'market_structure.parquet'}')
        ), fut AS (
          SELECT hs6,destination_code,bd_exports_to_destination_usd AS bd_y3
          FROM read_parquet('{y3/'bd_flows.parquet'}')
        )
        SELECT {y} AS year, {y-1} AS feature_year,
               prev.*, COALESCE(entry.bd_entry,0) AS bd_entry,
               base.market_base, COALESCE(fut.bd_y3,0) AS bd_y3
        FROM prev
        LEFT JOIN entry USING(hs6,destination_code)
        LEFT JOIN base USING(hs6,destination_code)
        LEFT JOIN fut USING(hs6,destination_code)
        WHERE prev.bd_prev < {entry_usd} AND COALESCE(entry.bd_entry,0) >= {entry_usd}
        """
        df = con.execute(sql).df()
        if df.empty:
            continue
        df["hs6"] = df["hs6"].astype(str).str.zfill(6)
        df["market_cagr_5y"] = safe_cagr(df["market_base"], df["destination_market_usd"], 5)
        df = _add_model_features(df, prod_usd="prod_usd", prod_dest="prod_dest", dest_usd="dest_usd")
        df["survives_3y"] = (df["bd_y3"] >= entry_usd).astype(int)
        frames.append(df)
    con.close()
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
