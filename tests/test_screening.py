import pandas as pd
from beod.screening import add_capability_screen


def test_capability_screen_does_not_call_distant_product_ready():
    df = pd.DataFrame([
        {
            'hs6':'870390','rca_bd':0.0003,'bd_exports_usd':50_000,'density_bd_percentile':0.15,
            'pci_percentile':0.89,'bd_market_share':0.0,'top_supplier_share':0.2,
            'market_growth_status':'stable_base','market_cagr_5y':0.1,'destination_market_usd':1e9,
        },
        {
            'hs6':'640399','rca_bd':3.3,'bd_exports_usd':50_000_000,'density_bd_percentile':0.96,
            'pci_percentile':0.17,'bd_market_share':0.004,'top_supplier_share':0.3,
            'market_growth_status':'stable_base','market_cagr_5y':0.1,'destination_market_usd':4e8,
        },
        {
            'hs6':'854460','rca_bd':0.00003,'bd_exports_usd':20_000,'density_bd_percentile':0.83,
            'pci_percentile':0.65,'bd_market_share':0.0,'top_supplier_share':0.25,
            'market_growth_status':'stable_base','market_cagr_5y':0.2,'destination_market_usd':2e9,
        },
        {
            'hs6':'180100','rca_bd':0.0,'bd_exports_usd':0,'density_bd_percentile':0.89,
            'pci_percentile':0.01,'bd_market_share':0.0,'top_supplier_share':0.25,
            'market_growth_status':'stable_base','market_cagr_5y':0.2,'destination_market_usd':3e9,
        },
    ])
    out=add_capability_screen(df)
    car=out.loc[out.hs6.eq('870390')].iloc[0]
    shoe=out.loc[out.hs6.eq('640399')].iloc[0]
    cable=out.loc[out.hs6.eq('854460')].iloc[0]
    cocoa=out.loc[out.hs6.eq('180100')].iloc[0]
    assert car.capability_status == 'distant_or_unobserved'
    assert car.screening_class == 'exploratory'
    assert shoe.screening_class == 'established_product_market_gap'
    assert cable.screening_class == 'adjacent_manufacturing_requires_validation'
    assert bool(cable.complexity_upgrade_flag)
    assert cocoa.screening_class == 'latent_endowment_or_other_requires_validation'
