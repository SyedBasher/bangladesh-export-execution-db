import pandas as pd
from beod.screening import add_capability_screen


def _base(**kw):
    x={
        'product_name':'generic manufactured product',
        'rca_bd':0.0,'bd_exports_usd':0.0,'bd_product_exports_usd':0.0,
        'bd_product_imports_usd':0.0,'bd_product_years_ge_100k_5y':0,
        'bd_product_years_ge_1m_5y':0,'density_bd_percentile':0.1,
        'pci_percentile':0.4,'bd_market_share':0.0,'top_supplier_share':0.2,
        'market_growth_status':'stable_base','market_cagr_5y':0.1,
        'destination_market_usd':1e9,
    }
    x.update(kw)
    return x


def test_capability_evidence_and_archetypes_are_not_overclaimed():
    df=pd.DataFrame([
        _base(hs6='870390',rca_bd=0.0003,bd_exports_usd=50_000,bd_product_exports_usd=50_000,
              density_bd_percentile=0.15,pci_percentile=0.89),
        _base(hs6='640399',product_name='footwear with leather uppers',rca_bd=3.3,
              bd_exports_usd=50_000_000,bd_product_exports_usd=50_000_000,
              bd_product_years_ge_100k_5y=5,bd_product_years_ge_1m_5y=5,
              density_bd_percentile=0.96,pci_percentile=0.17,bd_market_share=0.004),
        _base(hs6='854460',product_name='insulated electric conductors',rca_bd=0.00003,
              bd_exports_usd=20_000,bd_product_exports_usd=20_000,density_bd_percentile=0.83,
              pci_percentile=0.65),
        _base(hs6='740311',product_name='refined copper cathodes',rca_bd=0.0,
              density_bd_percentile=0.82,pci_percentile=0.4),
        _base(hs6='850440',product_name='electrical static converters',rca_bd=0.04,
              bd_exports_usd=8_000_000,bd_product_exports_usd=8_000_000,
              bd_product_years_ge_100k_5y=1,bd_product_years_ge_1m_5y=1,
              density_bd_percentile=0.7,pci_percentile=0.8),
        _base(hs6='930000',product_name='regulated product',rca_bd=2.0,
              bd_exports_usd=5_000_000,bd_product_exports_usd=5_000_000,
              bd_product_years_ge_100k_5y=5,bd_product_years_ge_1m_5y=5),
    ])
    out=add_capability_screen(df)
    car=out.loc[out.hs6.eq('870390')].iloc[0]
    shoe=out.loc[out.hs6.eq('640399')].iloc[0]
    cable=out.loc[out.hs6.eq('854460')].iloc[0]
    copper=out.loc[out.hs6.eq('740311')].iloc[0]
    converter=out.loc[out.hs6.eq('850440')].iloc[0]
    excluded=out.loc[out.hs6.eq('930000')].iloc[0]

    assert car.capability_status == 'distant_or_unobserved'
    assert car.screening_class == 'exploratory'
    assert shoe.capability_evidence_status == 'persistent_large'
    assert shoe.screening_class == 'established_product_market_gap'
    assert cable.screening_class == 'adjacent_downstream_manufacturing_requires_validation'
    assert bool(cable.complexity_upgrade_flag)
    assert copper.feasibility_archetype == 'process_capital_intensive'
    assert copper.screening_class == 'adjacent_process_industry_requires_validation'
    assert converter.capability_evidence_status == 'recent_large'
    assert converter.screening_class == 'recent_export_signal_requires_validation'
    assert excluded.screening_class == 'excluded_regulated_product'
