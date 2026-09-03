from __future__ import annotations
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from .features import pct_rank, safe_cagr


def make_transition_panel(agg_dir: Path, years: list[int], entry_usd: float = 100_000) -> pd.DataFrame:
    """
    Construct zero-to-entry observations using market structures plus Bangladesh flows.
    Outcome is entry above threshold within next three years. Designed for transparent
    out-of-time validation; no future information is used in features.
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
                   COALESCE(b.bd_exports_to_destination_usd,0) bd_now,
                   COALESCE(p.bd_product_exports_usd,0) prod_usd,
                   COALESCE(p.bd_product_destinations,0) prod_dest,
                   COALESCE(d.bd_destination_exports_usd,0) dest_usd
            FROM read_parquet('{yd/'market_structure.parquet'}') m
            LEFT JOIN read_parquet('{yd/'bd_flows.parquet'}') b USING(year,hs6,destination_code)
            LEFT JOIN read_parquet('{yd/'bd_product.parquet'}') p USING(year,hs6)
            LEFT JOIN read_parquet('{yd/'bd_destination.parquet'}') d USING(year,destination_code)
            WHERE m.destination_market_usd >= 5000000
          ), base AS (
            SELECT hs6,destination_code,destination_market_usd market_base
            FROM read_parquet('{y5/'market_structure.parquet'}')
          ), fut AS (
            SELECT hs6,destination_code, MAX(bd_exports_to_destination_usd) future_max
            FROM ({future_union}) GROUP BY 1,2
          )
          SELECT cur.*,base.market_base,COALESCE(fut.future_max,0) future_max
          FROM cur LEFT JOIN base USING(hs6,destination_code)
          LEFT JOIN fut USING(hs6,destination_code)
          WHERE cur.bd_now < {entry_usd}
        """
        df = con.execute(sql).df()
        df["market_cagr_5y"] = safe_cagr(df["market_base"], df["destination_market_usd"], 5)
        df["destination_familiarity"] = pct_rank(np.log1p(df["dest_usd"]))
        df["product_experience"] = (0.75*pct_rank(np.log1p(df["prod_usd"])) + 0.25*pct_rank(df["prod_dest"])).clip(0,1)
        df["log_market_usd"] = np.log1p(df["destination_market_usd"])
        df["entry_within_3y"] = (df["future_max"] >= entry_usd).astype(int)
        frames.append(df)
    con.close()
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def make_survival_panel(agg_dir: Path, years: list[int], entry_usd: float = 100_000) -> pd.DataFrame:
    """Historical new-entry cohorts and three-year survival outcomes.

    An entry at y is a market with Bangladesh exports below the threshold in y-1
    and at/above it in y. Survival is defined as exports at/above the same threshold
    in y+3. Features are measured at y, after entry is observed, and the model is
    explicitly conditional on entry. This is a predictive persistence model, not a
    causal estimate of export success.
    """
    frames=[]
    con=duckdb.connect()
    yearset=set(years)
    for y in years:
        if y-5 not in yearset or y-1 not in yearset or y+3 not in yearset:
            continue
        yd=agg_dir/f"year={y}"
        y1=agg_dir/f"year={y-1}"
        y5=agg_dir/f"year={y-5}"
        y3=agg_dir/f"year={y+3}"
        sql=f"""
        WITH cur AS (
          SELECT m.year,m.hs6,m.destination_code,m.destination_market_usd,m.supplier_hhi,m.top_supplier_share,
                 COALESCE(b.bd_exports_to_destination_usd,0) bd_now,
                 COALESCE(p.bd_product_exports_usd,0) prod_usd,
                 COALESCE(p.bd_product_destinations,0) prod_dest,
                 COALESCE(d.bd_destination_exports_usd,0) dest_usd
          FROM read_parquet('{yd/'market_structure.parquet'}') m
          LEFT JOIN read_parquet('{yd/'bd_flows.parquet'}') b USING(year,hs6,destination_code)
          LEFT JOIN read_parquet('{yd/'bd_product.parquet'}') p USING(year,hs6)
          LEFT JOIN read_parquet('{yd/'bd_destination.parquet'}') d USING(year,destination_code)
          WHERE m.destination_market_usd >= 5000000
        ), prev AS (
          SELECT hs6,destination_code,bd_exports_to_destination_usd bd_prev
          FROM read_parquet('{y1/'bd_flows.parquet'}')
        ), base AS (
          SELECT hs6,destination_code,destination_market_usd market_base
          FROM read_parquet('{y5/'market_structure.parquet'}')
        ), fut AS (
          SELECT hs6,destination_code,bd_exports_to_destination_usd bd_y3
          FROM read_parquet('{y3/'bd_flows.parquet'}')
        )
        SELECT cur.*,COALESCE(prev.bd_prev,0) bd_prev,base.market_base,COALESCE(fut.bd_y3,0) bd_y3
        FROM cur LEFT JOIN prev USING(hs6,destination_code)
                 LEFT JOIN base USING(hs6,destination_code)
                 LEFT JOIN fut USING(hs6,destination_code)
        WHERE COALESCE(prev.bd_prev,0) < {entry_usd} AND cur.bd_now >= {entry_usd}
        """
        df=con.execute(sql).df()
        if df.empty: continue
        df['market_cagr_5y']=safe_cagr(df['market_base'],df['destination_market_usd'],5)
        df['destination_familiarity']=pct_rank(np.log1p(df['dest_usd']))
        df['product_experience']=(0.75*pct_rank(np.log1p(df['prod_usd']))+0.25*pct_rank(df['prod_dest'])).clip(0,1)
        df['log_market_usd']=np.log1p(df['destination_market_usd'])
        df['survives_3y']=(df['bd_y3']>=entry_usd).astype(int)
        frames.append(df)
    con.close()
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
