#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
from beod.value_capture import load_value_capture_priors, attach_value_capture

pm=ROOT/'data/private/product_market_v02.parquet'
if not pm.exists(): pm=ROOT/'data/private/product_market_latest.parquet'
pri=ROOT/'data/external/value_capture_priors.csv'
if not pm.exists(): raise SystemExit('Run v0.1/v0.2 first.')
if not pri.exists(): raise SystemExit('Populate data/external/value_capture_priors.csv from a documented IO/SAM/TiVA source first. Template is in data/templates/.')
x=pd.read_parquet(pm)
p=load_value_capture_priors(pri)
y=attach_value_capture(x,p)
out=ROOT/'data/private/product_market_v04.parquet'
y.to_parquet(out,index=False,compression='zstd')
print(f'v0.4 rows: {len(y):,} -> {out}')
