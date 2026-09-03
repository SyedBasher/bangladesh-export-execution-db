#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
from beod.firm_registry import load_seed_registry, build_firm_capability_features, candidate_firm_matches

firms,links=load_seed_registry(ROOT/'data/seed')
f=build_firm_capability_features(firms,links)
out=ROOT/'data/public/firm_registry'
out.mkdir(parents=True,exist_ok=True)
f.to_csv(out/'firm_registry_seed.csv',index=False)
links.to_csv(out/'firm_product_links_seed.csv',index=False)
for df,name in [(f,'firm_registry_seed'),(links,'firm_product_links_seed')]:
    df.to_stata(out/f'{name}.dta',write_index=False,version=118)

pm=ROOT/'data/private/product_market_v02.parquet'
if not pm.exists(): pm=ROOT/'data/private/product_market_latest.parquet'
if pm.exists():
    m=candidate_firm_matches(pd.read_parquet(pm),f,links)
    private=ROOT/'data/private/firm_matches'
    private.mkdir(parents=True,exist_ok=True)
    m.to_parquet(private/'candidate_firm_matches.parquet',index=False,compression='zstd')
    print(f'private candidate firm-product-market matches: {len(m):,}')
print(f'firms={len(f):,}; observed firm-product links={len(links):,}')
