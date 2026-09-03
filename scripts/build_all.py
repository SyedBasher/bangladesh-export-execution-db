#!/usr/bin/env python3
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from beod.config import load_config
from beod.download import download_file, BACI_URL
from beod.build_core import build_metadata, build_annual_aggregates, build_latest_snapshot
from beod.export_formats import export_public, build_duckdb
from beod.training import make_transition_panel, make_survival_panel
from beod.models import temporal_validate_and_refit, score_model, save_model, save_reports


def main():
    cfg=load_config(ROOT/'config'/'build.yml')
    p=cfg['project']
    raw=ROOT/'data'/'raw'/f"BACI_HS12_V{p['baci_version']}.zip"
    download_file(BACI_URL,raw)
    agg=ROOT/'data'/'derived'/'annual'
    metadata=ROOT/'data'/'derived'/'metadata'
    build_metadata(raw,ROOT/'data'/'tmp',metadata)
    build_annual_aggregates(raw,ROOT/'data'/'tmp',agg,p['years'],p['bangladesh_baci_code'],p['baci_version'])
    snap=build_latest_snapshot(
        agg,ROOT/'data'/'private'/'product_market_latest.parquet',
        latest_year=max(p['years']),base_year=max(p['years'])-5,
        min_market_usd=cfg['thresholds']['min_destination_product_market_usd'],
        growth_base_min_usd=cfg['thresholds'].get('growth_base_min_usd',1_000_000),metadata_dir=metadata
    )

    entry_panel=make_transition_panel(agg,p['years'],cfg['thresholds']['entry_usd'])
    survival_panel=make_survival_panel(agg,p['years'],cfg['thresholds']['entry_usd'])
    model_dir=ROOT/'models'
    reports={}
    if len(entry_panel)>=cfg['thresholds']['min_model_observations'] and entry_panel['entry_within_3y'].nunique()==2:
        entry_model,latest_rep,rolling=temporal_validate_and_refit(entry_panel,'entry_within_3y')
        reports['entry_probability_3y']={
            'feature_timing':'features observed at cohort year y; outcome is entry in y+1..y+3',
            'latest_holdout':latest_rep,
            'rolling_holdouts':rolling,
        }
        save_model(entry_model,model_dir/'entry_probability_3y.pkl')
        snap['entry_probability_3y']=score_model(entry_model,snap)
        snap.loc[snap['bd_exports_to_destination_usd']>=cfg['thresholds']['entry_usd'],'entry_probability_3y']=pd.NA
    else:
        snap['entry_probability_3y']=pd.NA
    if len(survival_panel)>=max(100,cfg['thresholds']['min_model_observations']//5) and survival_panel['active_after_3y'].nunique()==2:
        surv_model,latest_rep,rolling=temporal_validate_and_refit(survival_panel,'active_after_3y')
        reports['persistence_probability_3y']={
            'feature_timing':'features observed at y-1, before the new entry at y; outcome is exports at/above the threshold in y+3; intervening years may be intermittent',
            'latest_holdout':latest_rep,
            'rolling_holdouts':rolling,
        }
        save_model(surv_model,model_dir/'persistence_probability_3y.pkl')
        snap['persistence_probability_3y']=score_model(surv_model,snap)
    else:
        snap['persistence_probability_3y']=pd.NA
    snap['durable_entry_score']=snap['entry_probability_3y'].astype('Float64')*snap['persistence_probability_3y'].astype('Float64')
    snap['model_specification']='v0.1.3: market structure + absolute and entity-ranked Bangladesh product/destination experience; public capability evidence adds five-year product persistence and import diagnostics; growth from de minimis historical bases is neutralized; persistence predictors are pre-entry'
    snap.to_parquet(ROOT/'data'/'private'/'product_market_latest.parquet',index=False,compression='zstd')
    if reports:
        save_reports(reports,model_dir/'validation_report.json')
    entry_panel.to_parquet(ROOT/'data'/'private'/'entry_training_panel.parquet',index=False,compression='zstd')
    survival_panel.to_parquet(ROOT/'data'/'private'/'survival_training_panel.parquet',index=False,compression='zstd')

    export_public(snap,ROOT/'data'/'public',cfg['public_release']['max_sample_rows'])
    build_duckdb(ROOT/'data'/'public',ROOT/'data'/'public'/'beoed_public.duckdb')
    print(f"Built {len(snap):,} latest-year product-market rows; entry cohorts={len(entry_panel):,}; survival cohorts={len(survival_panel):,}")
    for k,r in reports.items():
        print(k,r['latest_holdout'])

if __name__=='__main__':
    main()
