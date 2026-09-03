from pathlib import Path
import zipfile
import pandas as pd
import duckdb

from beod.build_core import build_metadata, build_annual_aggregates, build_latest_snapshot
from beod.export_formats import export_public, build_duckdb


def _write_csv(zf, name, rows):
    df = pd.DataFrame(rows)
    zf.writestr(name, df.to_csv(index=False))


def test_mini_pipeline(tmp_path: Path):
    zpath = tmp_path / "BACI_HS12_V202601.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for year, factor in [(2019, 1.0), (2024, 1.5)]:
            rows = [
                {"t": year, "k": "010101", "i": "050", "j": "276", "v": 100*factor, "q": 10*factor},
                {"t": year, "k": "010101", "i": "156", "j": "276", "v": 400*factor, "q": 40*factor},
                {"t": year, "k": "010101", "i": "356", "j": "276", "v": 200*factor, "q": 20*factor},
                {"t": year, "k": "020202", "i": "050", "j": "840", "v": 50*factor, "q": 5*factor},
                {"t": year, "k": "020202", "i": "156", "j": "840", "v": 350*factor, "q": 35*factor},
            ]
            _write_csv(zf, f"BACI_HS12_Y{year}_V202601.csv", rows)
        _write_csv(zf, "country_codes_V202601.csv", [
            {"country_code":"50", "country_name_full":"Bangladesh", "iso_3digit_alpha":"BGD"},
            {"country_code":"276", "country_name_full":"Germany", "iso_3digit_alpha":"DEU"},
            {"country_code":"840", "country_name_full":"United States", "iso_3digit_alpha":"USA"},
        ])
        _write_csv(zf, "product_codes_HS12_V202601.csv", [
            {"code":"010101", "description":"Illustrative product A"},
            {"code":"020202", "description":"Illustrative product B"},
        ])

    work = tmp_path / "tmp"
    meta = tmp_path / "meta"
    agg = tmp_path / "agg"
    build_metadata(zpath, work, meta)
    build_annual_aggregates(zpath, work, agg, [2019, 2024], bd_code=50, version="202601")
    snap = build_latest_snapshot(agg, tmp_path/"private/latest.parquet", latest_year=2024,
                                 base_year=2019, min_market_usd=1, metadata_dir=meta)
    assert set(snap["hs6"]) == {"010101", "020202"}
    assert "Germany" in set(snap["destination_name"].dropna())
    assert snap["bd_market_share"].between(0, 1).all()
    assert snap["market_attractiveness"].between(0, 100).all()

    public = tmp_path / "public"
    export_public(snap, public, sample_rows=10)
    build_duckdb(public, public/"beoed_public.duckdb")
    assert (public/"beoed_public_latest.parquet").exists()
    assert (public/"beoed_public_latest.dta").exists()
    con = duckdb.connect(str(public/"beoed_public.duckdb"), read_only=True)
    n = con.execute("select count(*) from public_latest").fetchone()[0]
    con.close()
    assert n == len(snap)
