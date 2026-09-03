from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, pickle
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    'log_market_usd','market_cagr_5y','supplier_hhi','top_supplier_share',
    'destination_familiarity','product_experience',
]

@dataclass
class ModelReport:
    n_train:int
    n_test:int
    event_rate_train:float
    event_rate_test:float
    auc:float|None
    brier:float|None
    train_years:str
    test_years:str


def make_logit() -> Pipeline:
    prep=ColumnTransformer([
        ('num',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),FEATURES)
    ])
    base=LogisticRegression(max_iter=2000,class_weight='balanced',C=0.5,random_state=42)
    return Pipeline([('prep',prep),('model',base)])


def make_calibrated():
    cv=StratifiedKFold(n_splits=3,shuffle=True,random_state=42)
    return CalibratedClassifierCV(make_logit(),method='sigmoid',cv=cv)


def fit_out_of_time(train:pd.DataFrame,test:pd.DataFrame,outcome:str):
    model=make_calibrated()
    model.fit(train[FEATURES],train[outcome].astype(int))
    p=model.predict_proba(test[FEATURES])[:,1]
    y=test[outcome].astype(int).to_numpy()
    auc=roc_auc_score(y,p) if len(np.unique(y))>1 else None
    brier=brier_score_loss(y,p) if len(y) else None
    rep=ModelReport(
        len(train),len(test),float(train[outcome].mean()),float(test[outcome].mean()),auc,brier,
        ','.join(map(str,sorted(train['year'].unique()))),','.join(map(str,sorted(test['year'].unique())))
    )
    return model,p,rep


def fit_all(df:pd.DataFrame,outcome:str):
    model=make_calibrated()
    model.fit(df[FEATURES],df[outcome].astype(int))
    return model


def temporal_validate_and_refit(panel:pd.DataFrame,outcome:str):
    if panel.empty: raise ValueError(f'No observations for {outcome}')
    years=sorted(panel['year'].dropna().astype(int).unique())
    if len(years)<2: raise ValueError('Need at least two cohort years for out-of-time validation')
    test_year=years[-1]
    train=panel[panel['year']<test_year].copy()
    test=panel[panel['year']==test_year].copy()
    if train[outcome].nunique()<2 or test[outcome].nunique()<2:
        # Expand holdout to latest two years if needed, still strictly later than train.
        if len(years)<3: raise ValueError('Insufficient outcome variation for temporal validation')
        cut=years[-2]
        train=panel[panel['year']<cut].copy()
        test=panel[panel['year']>=cut].copy()
    _,_,report=fit_out_of_time(train,test,outcome)
    final=fit_all(panel,outcome)
    return final,report


def score_model(model,df:pd.DataFrame) -> np.ndarray:
    return model.predict_proba(df[FEATURES])[:,1]


def save_model(model,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb') as f: pickle.dump(model,f)


def save_reports(reports:dict[str,ModelReport],path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({k:asdict(v) for k,v in reports.items()},indent=2),encoding='utf-8')
