#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
from beod.config import load_config
from beod.enrichments import add_v02_enrichments
from beod.product_space import compute_latest_complexity

cfg=load_config(ROOT/'config'/'build.yml')
p=cfg['project']; latest=max(p['years'])
base=ROOT/'data/private/product_market_latest.parquet'
cp=ROOT/'data/derived/annual'/f'year={latest}'/'country_product.parquet'
if not base.exists() or not cp.exists():
    raise SystemExit('Run scripts/build_all.py first; v0.2 needs the populated v0.1 snapshot and latest country-product matrix.')
x=pd.read_parquet(base)
c,pdprod=compute_latest_complexity(cp,p['bangladesh_baci_code'])
derived=ROOT/'data/derived/v02'; derived.mkdir(parents=True,exist_ok=True)
c.to_parquet(derived/'eci_latest.parquet',index=False,compression='zstd')
pdprod.to_parquet(derived/'product_space_latest.parquet',index=False,compression='zstd')
x['hs6']=x['hs6'].astype(str).str.zfill(6)
y=x.merge(pdprod[['hs6','pci','pci_rank','density_bd','rca_bd','bd_rca1','world_exports_usd']],on='hs6',how='left')
y=add_v02_enrichments(y,ROOT/'data/external')
out=ROOT/'data/private/product_market_v02.parquet'
y.to_parquet(out,index=False,compression='zstd')
print(f'v0.2 rows: {len(y):,}; product-space rows={len(pdprod):,}; countries={len(c):,}')
