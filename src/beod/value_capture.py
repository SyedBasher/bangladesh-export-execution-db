from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED = [
    'mapping_key','mapping_level','domestic_value_added_share','imported_input_share',
    'direct_labor_share','energy_intensity_index','credit_intensity_index',
    'source_year','source_name','mapping_confidence'
]


def load_value_capture_priors(path: Path) -> pd.DataFrame:
    x = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in x]
    if missing:
        raise ValueError(f'Missing value-capture fields: {missing}')
    for c in ['domestic_value_added_share','imported_input_share','direct_labor_share']:
        if ((x[c] < 0) | (x[c] > 1)).any():
            raise ValueError(f'{c} must lie in [0,1]')
    return x


def attach_value_capture(product_market: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    """Attach sector/product priors without pretending they are firm-specific outcomes."""
    out = product_market.copy()
    out['hs2'] = out['hs6'].astype(str).str.zfill(6).str[:2]
    # v0.4 template supports HS2 priors first. HS4/HS6 mappings can be layered later.
    p = priors[priors['mapping_level'].eq('HS2')].copy()
    p['mapping_key'] = p['mapping_key'].astype(str).str.zfill(2)
    out = out.merge(p, left_on='hs2', right_on='mapping_key', how='left')
    out['expected_domestic_value_capture_usd'] = out['bd_exports_to_destination_usd'] * out['domestic_value_added_share']
    out['expected_imported_input_content_usd'] = out['bd_exports_to_destination_usd'] * out['imported_input_share']
    out['value_capture_status'] = out['domestic_value_added_share'].notna().map({True:'sector_prior_attached',False:'no_prior'})
    return out
