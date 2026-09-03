from __future__ import annotations
from pathlib import Path
import shutil
import zipfile
import duckdb
import pandas as pd
import numpy as np

from .features import safe_cagr, add_experience_features, add_absolute_model_features, add_transparent_indices, diagnostic_flags


def _extract_member(zf: zipfile.ZipFile, member: str, temp_dir: Path) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    target = temp_dir / Path(member).name
    with zf.open(member) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
    return target


def _repair_mojibake(value):
    """Repair common UTF-8-as-Latin-1 mojibake without changing valid Unicode."""
    if pd.isna(value):
        return pd.NA
    s = str(value)
    bad = ("Ã", "Â", "â€", "ðŸ")
    if not any(marker in s for marker in bad):
        return s
    try:
        candidate = s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    before = sum(s.count(x) for x in bad)
    after = sum(candidate.count(x) for x in bad)
    return candidate if after < before else s


def _clean_text_series(s: pd.Series) -> pd.Series:
    return s.map(_repair_mojibake).astype("string")


def build_metadata(zip_path: Path, work_dir: Path, out_dir: Path) -> tuple[Path | None, Path | None]:
    """Extract and normalize BACI country/product metadata bundled with the archive."""
    out_dir.mkdir(parents=True, exist_ok=True)
    country_out = out_dir / "countries.parquet"
    product_out = out_dir / "products.parquet"
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        country_members = [n for n in names if "country_codes" in n.lower() and n.lower().endswith(".csv")]
        product_members = [n for n in names if "product_codes" in n.lower() and n.lower().endswith(".csv")]

        if country_members:
            f = _extract_member(zf, country_members[0], work_dir)
            c = pd.read_csv(f, dtype=str, encoding="utf-8-sig")
            lower = {x.lower(): x for x in c.columns}
            code_col = next((lower[k] for k in ["country_code", "code"] if k in lower), c.columns[0])
            name_col = next((lower[k] for k in ["country_name_full", "country_name", "name"] if k in lower), None)
            iso3_col = next(
                (lower[k] for k in ["country_iso3", "iso_3digit_alpha", "iso3", "iso_alpha3"] if k in lower),
                None,
            )
            if name_col:
                iso = _clean_text_series(c[iso3_col]).str.upper() if iso3_col else pd.Series(pd.NA, index=c.index, dtype="string")
                iso = iso.where(iso.str.fullmatch(r"[A-Z]{3}", na=False), pd.NA)
                out = pd.DataFrame({
                    "country_code": pd.to_numeric(c[code_col], errors="coerce").astype("Int64"),
                    "country_name": _clean_text_series(c[name_col]),
                    "iso3": iso,
                }).dropna(subset=["country_code"])
                out = out.drop_duplicates("country_code")
                out.to_parquet(country_out, index=False, compression="zstd")
            f.unlink(missing_ok=True)

        if product_members:
            f = _extract_member(zf, product_members[0], work_dir)
            h = pd.read_csv(f, dtype=str, encoding="utf-8-sig")
            lower = {x.lower(): x for x in h.columns}
            code_col = next((lower[k] for k in ["code", "product_code", "hs6"] if k in lower), h.columns[0])
            desc_col = next((lower[k] for k in ["description", "product_name", "name"] if k in lower), None)
            if desc_col:
                out = pd.DataFrame({
                    "hs6": h[code_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6),
                    "product_name": _clean_text_series(h[desc_col]),
                }).drop_duplicates("hs6")
                out.to_parquet(product_out, index=False, compression="zstd")
            f.unlink(missing_ok=True)
    return (country_out if country_out.exists() else None,
            product_out if product_out.exists() else None)


def build_annual_aggregates(zip_path: Path, work_dir: Path, out_dir: Path,
                            years: list[int], bd_code: int = 50,
                            version: str = "202601"):
    """Build compact annual BACI aggregates without retaining the global row panel."""
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for year in years:
            expected = f"BACI_HS12_Y{year}_V{version}.csv"
            matches = [n for n in names if n.endswith(expected)]
            if not matches:
                raise FileNotFoundError(expected)
            csv_path = _extract_member(zf, matches[0], work_dir)
            ydir = out_dir / f"year={year}"
            ydir.mkdir(parents=True, exist_ok=True)
            qcsv = str(csv_path).replace("'", "''")
            con.execute(f"""
                CREATE OR REPLACE TEMP VIEW raw AS
                SELECT CAST(t AS INTEGER) AS "year",
                       LPAD(CAST(k AS VARCHAR), 6, '0') AS hs6,
                       CAST(i AS INTEGER) AS exporter_code,
                       CAST(j AS INTEGER) AS destination_code,
                       CAST(v AS DOUBLE) * 1000.0 AS value_usd,
                       TRY_CAST(q AS DOUBLE) AS quantity
                FROM read_csv_auto('{qcsv}', header=true, all_varchar=true);
            """)
            con.execute(f"""
                COPY (
                    SELECT year, hs6, destination_code,
                           SUM(value_usd) AS bd_exports_to_destination_usd,
                           SUM(quantity) AS bd_export_qty
                    FROM raw WHERE exporter_code={bd_code}
                    GROUP BY 1,2,3
                ) TO '{ydir / 'bd_flows.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);
            """)
            con.execute(f"""
                COPY (
                    WITH s AS (
                      SELECT year, hs6, destination_code, exporter_code,
                             SUM(value_usd) AS supplier_value
                      FROM raw GROUP BY 1,2,3,4
                    ), z AS (
                      SELECT *,
                             supplier_value / NULLIF(SUM(supplier_value) OVER(PARTITION BY year,hs6,destination_code),0) AS supplier_share,
                             ROW_NUMBER() OVER(PARTITION BY year,hs6,destination_code ORDER BY supplier_value DESC, exporter_code) AS rn
                      FROM s
                    )
                    SELECT year, hs6, destination_code,
                           SUM(supplier_value) AS destination_market_usd,
                           SUM(supplier_share*supplier_share) AS supplier_hhi,
                           MAX(CASE WHEN rn=1 THEN exporter_code END) AS top_supplier_code,
                           MAX(CASE WHEN rn=1 THEN supplier_share END) AS top_supplier_share
                    FROM z GROUP BY 1,2,3
                ) TO '{ydir / 'market_structure.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);
            """)
            con.execute(f"""
                COPY (
                    WITH ex AS (
                      SELECT year, hs6,
                             SUM(value_usd) AS bd_product_exports_usd,
                             COUNT(DISTINCT destination_code) AS bd_product_destinations
                      FROM raw WHERE exporter_code={bd_code}
                      GROUP BY 1,2
                    ), im AS (
                      SELECT year, hs6,
                             SUM(value_usd) AS bd_product_imports_usd,
                             COUNT(DISTINCT exporter_code) AS bd_product_import_origins
                      FROM raw WHERE destination_code={bd_code}
                      GROUP BY 1,2
                    )
                    SELECT COALESCE(ex.year,im.year) AS year,
                           COALESCE(ex.hs6,im.hs6) AS hs6,
                           COALESCE(ex.bd_product_exports_usd,0) AS bd_product_exports_usd,
                           COALESCE(ex.bd_product_destinations,0) AS bd_product_destinations,
                           COALESCE(im.bd_product_imports_usd,0) AS bd_product_imports_usd,
                           COALESCE(im.bd_product_import_origins,0) AS bd_product_import_origins
                    FROM ex FULL OUTER JOIN im USING(year,hs6)
                ) TO '{ydir / 'bd_product.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);
            """)
            con.execute(f"""
                COPY (
                    SELECT year, destination_code,
                           SUM(value_usd) AS bd_destination_exports_usd
                    FROM raw WHERE exporter_code={bd_code}
                    GROUP BY 1,2
                ) TO '{ydir / 'bd_destination.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);
            """)
            if year == max(years):
                con.execute(f"""
                    COPY (
                        SELECT year, exporter_code AS country_code, hs6,
                               SUM(value_usd) AS export_value_usd
                        FROM raw GROUP BY 1,2,3
                    ) TO '{ydir / 'country_product.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);
                """)
            csv_path.unlink(missing_ok=True)
    con.close()


def build_latest_snapshot(agg_dir: Path, out_file: Path, latest_year: int = 2024,
                          base_year: int = 2019, min_market_usd: float = 5_000_000,
                          growth_base_min_usd: float = 1_000_000,
                          metadata_dir: Path | None = None):
    con = duckdb.connect()
    ly = agg_dir / f"year={latest_year}"
    by = agg_dir / f"year={base_year}"
    sql = f"""
      WITH cur AS (
        SELECT m.year, m.hs6, m.destination_code, m.destination_market_usd,
               m.supplier_hhi, m.top_supplier_code, m.top_supplier_share,
               COALESCE(b.bd_exports_to_destination_usd,0) AS bd_exports_to_destination_usd,
               COALESCE(p.bd_product_exports_usd,0) AS bd_product_exports_usd,
               COALESCE(p.bd_product_destinations,0) AS bd_product_destinations,
               COALESCE(p.bd_product_imports_usd,0) AS bd_product_imports_usd,
               COALESCE(p.bd_product_import_origins,0) AS bd_product_import_origins,
               COALESCE(d.bd_destination_exports_usd,0) AS bd_destination_exports_usd
        FROM read_parquet('{ly / 'market_structure.parquet'}') m
        LEFT JOIN read_parquet('{ly / 'bd_flows.parquet'}') b USING(year,hs6,destination_code)
        LEFT JOIN read_parquet('{ly / 'bd_product.parquet'}') p USING(year,hs6)
        LEFT JOIN read_parquet('{ly / 'bd_destination.parquet'}') d USING(year,destination_code)
        WHERE m.destination_market_usd >= {min_market_usd}
      ), base AS (
        SELECT hs6,destination_code,destination_market_usd AS market_base_usd_5y
        FROM read_parquet('{by / 'market_structure.parquet'}')
      ), hist AS (
        SELECT hs6,
               COUNT(*) FILTER (WHERE bd_product_exports_usd > 0) AS bd_product_positive_years_5y,
               COUNT(*) FILTER (WHERE bd_product_exports_usd >= 100000) AS bd_product_years_ge_100k_5y,
               COUNT(*) FILTER (WHERE bd_product_exports_usd >= 1000000) AS bd_product_years_ge_1m_5y,
               SUM(bd_product_exports_usd) AS bd_product_exports_5y_total_usd,
               MAX(bd_product_exports_usd) AS bd_product_exports_5y_max_usd
        FROM read_parquet('{agg_dir / 'year=*' / 'bd_product.parquet'}')
        WHERE year BETWEEN {latest_year-4} AND {latest_year}
        GROUP BY 1
      )
      SELECT cur.*, base.market_base_usd_5y,
             COALESCE(hist.bd_product_positive_years_5y,0) AS bd_product_positive_years_5y,
             COALESCE(hist.bd_product_years_ge_100k_5y,0) AS bd_product_years_ge_100k_5y,
             COALESCE(hist.bd_product_years_ge_1m_5y,0) AS bd_product_years_ge_1m_5y,
             COALESCE(hist.bd_product_exports_5y_total_usd,0) AS bd_product_exports_5y_total_usd,
             COALESCE(hist.bd_product_exports_5y_max_usd,0) AS bd_product_exports_5y_max_usd
      FROM cur
      LEFT JOIN base USING(hs6,destination_code)
      LEFT JOIN hist USING(hs6)
    """
    df = con.execute(sql).df()
    con.close()
    df["hs6"] = df["hs6"].astype(str).str.zfill(6)
    df["bd_market_share"] = df["bd_exports_to_destination_usd"] / df["destination_market_usd"].replace(0, np.nan)
    df["market_cagr_5y"] = safe_cagr(df["market_base_usd_5y"], df["destination_market_usd"], latest_year-base_year)
    df["bd_product_exports_5y_mean_usd"] = df["bd_product_exports_5y_total_usd"] / 5.0
    df["bd_product_net_exports_usd"] = df["bd_product_exports_usd"] - df["bd_product_imports_usd"]
    df["bd_product_log_export_import_ratio"] = (
        np.log1p(pd.to_numeric(df["bd_product_exports_usd"],errors="coerce").fillna(0).clip(lower=0))
        - np.log1p(pd.to_numeric(df["bd_product_imports_usd"],errors="coerce").fillna(0).clip(lower=0))
    )
    df = add_experience_features(df)
    df = add_absolute_model_features(df)
    df["log_market_usd"] = np.log1p(df["destination_market_usd"])
    df = add_transparent_indices(df, base_col="market_base_usd_5y", growth_base_min_usd=growth_base_min_usd)
    df["diagnostic_flags"] = df.apply(diagnostic_flags, axis=1)
    if metadata_dir is not None:
        cfile = metadata_dir / "countries.parquet"
        pfile = metadata_dir / "products.parquet"
        if cfile.exists():
            c = pd.read_parquet(cfile).rename(columns={"country_code": "destination_code", "country_name": "destination_name"})
            df = df.merge(c[["destination_code", "destination_name", "iso3"]], on="destination_code", how="left", validate="many_to_one")
        if pfile.exists():
            h = pd.read_parquet(pfile)
            df = df.merge(h[["hs6", "product_name"]], on="hs6", how="left", validate="many_to_one")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_file, index=False, compression="zstd")
    return df
