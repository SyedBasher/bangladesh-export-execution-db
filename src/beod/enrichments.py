from __future__ import annotations
from pathlib import Path
import pandas as pd


def _read_any(path: Path) -> pd.DataFrame:
    suf = path.suffix.lower()
    if suf in {'.csv', '.gz'} or path.name.endswith('.csv.gz'):
        return pd.read_csv(path, dtype={'hs6': str})
    if suf == '.parquet':
        return pd.read_parquet(path)
    if suf == '.dta':
        return pd.read_stata(path, convert_categoricals=False)
    raise ValueError(f'Unsupported external format: {path}')


def normalize_hs6(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)


def add_v02_enrichments(base: pd.DataFrame, external_dir: Path) -> pd.DataFrame:
    """Join optional v0.2 sources to the product-market snapshot.

    Expected optional files (CSV/Parquet/DTA):
      tariffs_hs6_destination.* : hs6, destination_code, tariff_year,
          mfn_tariff, preferential_tariff, preference_margin
      product_space.* : hs6, pci, density_bd, complexity_rank
      gravity.* : destination_code, gravity_year, trade_cost_index,
          distance_km, common_language, colonial_link

    Missing sources do not abort the build. Provenance flags make absence explicit.
    """
    out = base.copy()
    out['hs6'] = normalize_hs6(out['hs6'])

    def first(stems):
        for stem in stems:
            for ext in ['parquet','csv','csv.gz','dta']:
                p = external_dir / f'{stem}.{ext}'
                if p.exists(): return p
        return None

    tpath = first(['tariffs_hs6_destination'])
    if tpath:
        t = _read_any(tpath)
        t['hs6'] = normalize_hs6(t['hs6'])
        keep = [c for c in ['hs6','destination_code','tariff_year','mfn_tariff','preferential_tariff','preference_margin','tariff_source'] if c in t]
        out = out.merge(t[keep].drop_duplicates(['hs6','destination_code']), on=['hs6','destination_code'], how='left')
        out['tariff_data_status'] = out['mfn_tariff'].notna().map({True:'observed',False:'missing'}) if 'mfn_tariff' in out else 'missing'
    else:
        out['tariff_data_status'] = 'source_not_loaded'

    ppath = first(['product_space'])
    if ppath:
        p = _read_any(ppath)
        p['hs6'] = normalize_hs6(p['hs6'])
        keep = [c for c in ['hs6','pci','density_bd','complexity_rank','product_space_year','product_space_source'] if c in p]
        out = out.merge(p[keep].drop_duplicates('hs6'), on='hs6', how='left')
        out['product_space_status'] = out['pci'].notna().map({True:'observed_or_derived',False:'missing'}) if 'pci' in out else 'missing'
    else:
        out['product_space_status'] = 'source_not_loaded'

    gpath = first(['gravity'])
    if gpath:
        g = _read_any(gpath)
        keep = [c for c in ['destination_code','gravity_year','trade_cost_index','distance_km','common_language','colonial_link','gravity_source'] if c in g]
        out = out.merge(g[keep].drop_duplicates('destination_code'), on='destination_code', how='left')
        out['gravity_data_status'] = out['distance_km'].notna().map({True:'observed_or_derived',False:'missing'}) if 'distance_km' in out else 'missing'
    else:
        out['gravity_data_status'] = 'source_not_loaded'

    # Deliberately do not collapse these into a black-box score.
    return out
