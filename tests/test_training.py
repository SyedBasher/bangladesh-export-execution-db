from pathlib import Path
import pandas as pd
from beod.training import make_survival_panel


def _write_year(root: Path, year: int, market=None, flow=None, product=None, destination=None):
    ydir=root/f'year={year}'; ydir.mkdir(parents=True,exist_ok=True)
    if market is not None:
        pd.DataFrame(market).to_parquet(ydir/'market_structure.parquet',index=False)
    if flow is not None:
        pd.DataFrame(flow).to_parquet(ydir/'bd_flows.parquet',index=False)
    if product is not None:
        pd.DataFrame(product).to_parquet(ydir/'bd_product.parquet',index=False)
    if destination is not None:
        pd.DataFrame(destination).to_parquet(ydir/'bd_destination.parquet',index=False)


def test_survival_features_are_pre_entry(tmp_path: Path):
    hs='123456'; dest=276
    _write_year(tmp_path,2012,
        market=[{'year':2012,'hs6':hs,'destination_code':dest,'destination_market_usd':5_000_000,'supplier_hhi':0.4,'top_supplier_code':1,'top_supplier_share':0.5}])
    _write_year(tmp_path,2017,
        market=[{'year':2017,'hs6':hs,'destination_code':dest,'destination_market_usd':10_000_000,'supplier_hhi':0.2,'top_supplier_code':1,'top_supplier_share':0.3}],
        flow=[{'year':2017,'hs6':hs,'destination_code':dest,'bd_exports_to_destination_usd':50_000,'bd_export_qty':1}],
        product=[{'year':2017,'hs6':hs,'bd_product_exports_usd':500_000,'bd_product_destinations':2}],
        destination=[{'year':2017,'destination_code':dest,'bd_destination_exports_usd':1_000_000}])
    _write_year(tmp_path,2018,
        flow=[{'year':2018,'hs6':hs,'destination_code':dest,'bd_exports_to_destination_usd':200_000,'bd_export_qty':2}])
    _write_year(tmp_path,2021,
        flow=[{'year':2021,'hs6':hs,'destination_code':dest,'bd_exports_to_destination_usd':150_000,'bd_export_qty':2}])
    panel=make_survival_panel(tmp_path,[2012,2017,2018,2021],entry_usd=100_000)
    assert len(panel)==1
    r=panel.iloc[0]
    assert int(r['year'])==2018
    assert int(r['feature_year'])==2017
    assert r['destination_market_usd']==10_000_000
    assert r['bd_prev']==50_000
    assert r['bd_entry']==200_000
    assert r['active_after_3y']==1
