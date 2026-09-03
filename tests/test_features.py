import pandas as pd
from beod.features import add_transparent_indices, diagnostic_flags


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
    r = pd.Series({"market_cagr_5y":-0.1,"top_supplier_share":0.7,"destination_familiarity":0.1,"product_experience":0.2,"bd_market_share":0.0})
    f = diagnostic_flags(r)
    assert "declining_market" in f and "high_supplier_concentration" in f
