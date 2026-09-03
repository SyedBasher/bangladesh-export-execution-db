#!/usr/bin/env python3
from pathlib import Path
import json, datetime
ROOT=Path(__file__).resolve().parents[1]
paths={
 'public_latest':'data/public/beoed_public_latest.parquet',
 'public_screening_v02':'data/public/beoed_public_screening_v02.parquet',
 'sample_established_gaps':'data/public/beoed_established_product_market_gaps_sample.csv',
 'sample_emerging_products':'data/public/beoed_emerging_products_sample.csv',
 'sample_adjacent_manufacturing':'data/public/beoed_adjacent_manufacturing_sample.csv',
 'sample_recent_export_signals':'data/public/beoed_recent_export_signals_sample.csv',
 'sample_process_industry_validation':'data/public/beoed_process_industry_validation_sample.csv',
 'sample_advanced_technology_validation':'data/public/beoed_advanced_technology_validation_sample.csv',
 'public_csv':'data/public/beoed_public_latest.csv.gz',
 'public_stata':'data/public/beoed_public_latest.dta',
 'public_duckdb':'data/public/beoed_public.duckdb',
 'firm_registry':'data/public/firm_registry/firm_registry_seed.csv',
 'firm_product_links':'data/public/firm_registry/firm_product_links_seed.csv',
 'complexity':'data/derived/v02/product_space_latest.parquet',
 'eci':'data/derived/v02/eci_latest.parquet',
 'validation':'models/validation_report.json',
 'qa':'models/qa_report.json',
}
manifest={
 'built_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'baci_release':'202601',
 'hs_revision':'HS2012',
 'beoed_schema_version':'v0.1.3',
 'release_status':'QA build; not a public opportunity ranking',
 'files':{},
}
for k,rel in paths.items():
 p=ROOT/rel
 manifest['files'][k]={'path':rel,'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None}
qa=ROOT/'models/qa_report.json'
if qa.exists():
 q=json.loads(qa.read_text(encoding='utf-8'))
 manifest['qa_pass']=q.get('qa_pass')
 manifest['qa_summary']={
     'critical_failures':q.get('critical_failures',[]),
     'warnings':q.get('warnings',[]),
     'public_summary':q.get('public_summary'),
     'v02_summary':q.get('v02_summary'),
     'duckdb_summary':q.get('duckdb_summary'),
     'model_quality_summary':q.get('model_quality_summary'),
 }
(ROOT/'release_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
