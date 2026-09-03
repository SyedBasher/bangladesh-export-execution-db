#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from beod.config import load_config
from beod.qa import audit_release, write_qa_report

cfg=load_config(ROOT/'config'/'build.yml')
p=cfg['project']; latest=max(p['years'])
report=audit_release(
    public_path=ROOT/'data/public/beoed_public_latest.parquet',
    v02_path=ROOT/'data/public/beoed_public_screening_v02.parquet',
    duckdb_path=ROOT/'data/public/beoed_public.duckdb',
    annual_bd_flows_path=ROOT/'data/derived/annual'/f'year={latest}'/'bd_flows.parquet',
    eci_path=ROOT/'data/derived/v02/eci_latest.parquet',
    validation_path=ROOT/'models/validation_report.json',
    min_market_usd=cfg['thresholds']['min_destination_product_market_usd'],
)
write_qa_report(report,ROOT/'models/qa_report.json')
print(report)
if not report['qa_pass']:
    raise SystemExit('QA FAILED: '+ ' | '.join(report['critical_failures']))
