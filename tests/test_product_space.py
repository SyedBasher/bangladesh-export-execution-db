from pathlib import Path
from unittest.mock import patch
import pandas as pd
from beod.product_space import compute_latest_complexity


def test_product_space_synthetic():
    synthetic=pd.DataFrame({
      'country_code':[50,50,50,1,1,1,2,2,2,3,3,3],
      'hs6':['000001','000002','000003']*4,
      'export_value_usd':[100,50,5,20,300,10,200,40,100,10,20,400]
    })
    with patch('pandas.read_parquet', return_value=synthetic):
        c,p=compute_latest_complexity(Path('dummy.parquet'),bd_code=50)
    assert len(c)==4
    assert len(p)==3
    assert p['density_bd'].between(0,1).all()
