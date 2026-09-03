import pandas as pd
from beod.features import add_transparent_indices, diagnostic_flags, add_experience_features


def test_indices_bounds():
    df = pd.DataFrame({
        "destination_market_usd": [5e6, 20e6, 100e6],
        "market_cagr_5y": [-0.02, 0.05, 0.20],
        "supplier_hhi": [0.8, 0.3, 0.1],
        "product_experience": [0.1, 0.5, 0.9],
        "destination_familiarity": [0.2, 0.6, 0.8],
    })
    out = add_transparent_indices(df)
    assert out["market_attractiveness"].between(0, 100).all()
    assert out["readiness_index"].between(0, 100).all()


def test_flags():
    r = pd.Series({"market_cagr_5y":-0.1,"top_supplier_share":0.7,"destination_familiarity":0.1,"product_experience":0.2,"bd_market_share":0.0,"bd_exports_to_destination_usd":0})
    f = diagnostic_flags(r)
    assert "declining_market" in f and "high_supplier_concentration" in f and "no_current_bd_exports" in f


def test_experience_ranks_unique_entities_not_repeated_rows():
    df = pd.DataFrame({
        'hs6':['A','A','A','B'],
        'destination_code':[1,2,3,3],
        'bd_product_exports_usd':[100,100,100,1000],
        'bd_product_destinations':[3,3,3,1],
        'bd_destination_exports_usd':[10,20,100,100],
    })
    out = add_experience_features(df)
    # Same product/destination must always receive exactly one score.
    assert out.groupby('hs6')['product_experience'].nunique().max() == 1
    assert out.groupby('destination_code')['destination_familiarity'].nunique().max() == 1
    # Destination 3 is highest among the three unique destinations; duplicate rows do not alter that.
    assert out.loc[out.destination_code.eq(3),'destination_familiarity'].iloc[0] == 1.0
