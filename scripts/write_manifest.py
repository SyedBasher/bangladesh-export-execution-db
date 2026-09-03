#!/usr/bin/env python3
from pathlib import Path
import json, datetime
ROOT=Path(__file__).resolve().parents[1]
paths={
 'public_latest':'data/public/beoed_public_latest.parquet',
 'public_csv':'data/public/beoed_public_latest.csv.gz',
 'public_stata':'data/public/beoed_public_latest.dta',
 'public_duckdb':'data/public/beoed_public.duckdb',
 'firm_registry':'data/public/firm_registry/firm_registry_seed.csv',
 'firm_product_links':'data/public/firm_registry/firm_product_links_seed.csv',
 'complexity':'data/derived/v02/product_space_latest.parquet',
 'validation':'models/validation_report.json',
}
manifest={'built_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baci_release':'202601','hs_revision':'HS2012','files':{}}
for k,rel in paths.items():
 p=ROOT/rel
 manifest['files'][k]={'path':rel,'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None}
(ROOT/'release_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
