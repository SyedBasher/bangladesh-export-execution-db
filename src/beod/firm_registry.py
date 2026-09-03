from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np


def load_seed_registry(seed_dir: Path):
    firms = pd.read_csv(seed_dir/'firm_registry_seed.csv')
    links = pd.read_csv(seed_dir/'firm_product_links_seed.csv', dtype={'observed_hs_code':str,'hs4':str,'hs2':str})
    for c in ['observed_hs_code','hs4','hs2']:
        links[c] = links[c].astype(str).str.replace(r'\.0$','',regex=True).str.zfill({'observed_hs_code':4,'hs4':4,'hs2':2}[c])
    return firms, links


def build_firm_capability_features(firms: pd.DataFrame, links: pd.DataFrame):
    """Manufacture conservative capability descriptors from observed EPB links.

    These are descriptive registry features, not production-capability claims.
    """
    x = links.copy()
    agg = (x.groupby('epb_exporter_id')
             .agg(observed_hs4_count=('hs4','nunique'), observed_hs2_count=('hs2','nunique'))
             .reset_index())
    out = firms.merge(agg,on='epb_exporter_id',how='left')
    out['observed_hs4_count'] = out['observed_hs4_count'].fillna(0).astype(int)
    out['observed_hs2_count'] = out['observed_hs2_count'].fillna(0).astype(int)
    out['capability_breadth_percentile'] = out['observed_hs4_count'].rank(pct=True, method='average')
    out['multi_chapter_observed'] = out['observed_hs2_count'].ge(2)
    out['capability_interpretation'] = np.where(
        out['multi_chapter_observed'],
        'observed registrations span multiple HS chapters; investigate transferable capability',
        'observed registrations concentrated in one HS chapter'
    )
    out['inference_limit'] = 'EPB registration indicates observed product linkage; it does not prove current capacity, scale, destination, or certification.'
    return out


def candidate_firm_matches(product_market: pd.DataFrame, firms: pd.DataFrame, links: pd.DataFrame):
    """Generate conservative HS4 firm matches for commissioned investigation.

    Match status is 'observed_related_hs4', never 'can_produce'.
    """
    pm = product_market.copy()
    pm['hs4'] = pm['hs6'].astype(str).str.zfill(6).str[:4]
    l = links[['epb_exporter_id','hs4']].drop_duplicates()
    m = pm.merge(l,on='hs4',how='inner').merge(
        firms[['epb_exporter_id','company_name','district','confidence_grade']],
        on='epb_exporter_id',how='left'
    )
    m['firm_match_status'] = 'observed_related_hs4'
    m['firm_match_claim'] = 'candidate for investigation, not verified production capability'
    return m
