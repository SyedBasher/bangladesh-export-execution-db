from __future__ import annotations
from dataclasses import dataclass, asdict, is_dataclass
from pathlib import Path
import json, pickle
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "log_market_usd","market_cagr_5y","supplier_hhi","top_supplier_share",
    "destination_familiarity","product_experience",
    "log_product_exports_usd","log_destination_exports_usd","log_product_destinations",
]


@dataclass
class ModelReport:
    n_train: int
    n_test: int
    event_rate_train: float
    event_rate_test: float
    auc: float | None
    pr_auc: float | None
    brier: float | None
    brier_baseline: float | None
    brier_skill: float | None
    top_5pct_precision: float | None
    top_5pct_lift: float | None
    top_5pct_event_capture: float | None
    calibration_intercept: float | None
    calibration_slope: float | None
    ece_10bin: float | None
    train_years: str
    test_years: str


def make_logit() -> Pipeline:
    prep = ColumnTransformer([
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), FEATURES)
    ])
    base = LogisticRegression(max_iter=2000, class_weight="balanced", C=0.5, random_state=42)
    return Pipeline([("prep", prep), ("model", base)])


def make_calibrated():
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    return CalibratedClassifierCV(make_logit(), method="sigmoid", cv=cv)


def _calibration_intercept_slope(y: np.ndarray, p: np.ndarray) -> tuple[float | None, float | None]:
    if len(np.unique(y)) < 2:
        return None, None
    eps = 1e-6
    pp = np.clip(p, eps, 1-eps)
    logit = np.log(pp / (1-pp)).reshape(-1, 1)
    try:
        m = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000)
        m.fit(logit, y)
        return float(m.intercept_[0]), float(m.coef_[0][0])
    except Exception:
        return None, None


def _ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float | None:
    if len(y) == 0:
        return None
    d = pd.DataFrame({"y": y, "p": p})
    try:
        d["bin"] = pd.qcut(d["p"], q=min(bins, d["p"].nunique()), duplicates="drop")
    except ValueError:
        return None
    g = d.groupby("bin", observed=True).agg(n=("y","size"), obs=("y","mean"), pred=("p","mean"))
    if g.empty:
        return None
    return float(((g["n"] / g["n"].sum()) * (g["obs"] - g["pred"]).abs()).sum())


def _evaluate(y: np.ndarray, p: np.ndarray) -> dict:
    prevalence = float(np.mean(y)) if len(y) else np.nan
    auc = roc_auc_score(y, p) if len(np.unique(y)) > 1 else None
    pr = average_precision_score(y, p) if len(np.unique(y)) > 1 else None
    brier = brier_score_loss(y, p) if len(y) else None
    baseline = prevalence * (1-prevalence) if np.isfinite(prevalence) else None
    skill = (1 - brier / baseline) if brier is not None and baseline and baseline > 0 else None

    n_top = max(1, int(np.ceil(0.05 * len(y)))) if len(y) else 0
    if n_top:
        idx = np.argsort(-p)[:n_top]
        precision = float(np.mean(y[idx]))
        lift = precision / prevalence if prevalence > 0 else None
        capture = float(np.sum(y[idx]) / np.sum(y)) if np.sum(y) > 0 else None
    else:
        precision = lift = capture = None
    cint, cslope = _calibration_intercept_slope(y, p)
    return {
        "auc": float(auc) if auc is not None else None,
        "pr_auc": float(pr) if pr is not None else None,
        "brier": float(brier) if brier is not None else None,
        "brier_baseline": float(baseline) if baseline is not None else None,
        "brier_skill": float(skill) if skill is not None else None,
        "top_5pct_precision": precision,
        "top_5pct_lift": float(lift) if lift is not None else None,
        "top_5pct_event_capture": capture,
        "calibration_intercept": cint,
        "calibration_slope": cslope,
        "ece_10bin": _ece(y, p, 10),
    }


def fit_out_of_time(train: pd.DataFrame, test: pd.DataFrame, outcome: str):
    model = make_calibrated()
    model.fit(train[FEATURES], train[outcome].astype(int))
    p = model.predict_proba(test[FEATURES])[:, 1]
    y = test[outcome].astype(int).to_numpy()
    metrics = _evaluate(y, p)
    rep = ModelReport(
        n_train=len(train),
        n_test=len(test),
        event_rate_train=float(train[outcome].mean()),
        event_rate_test=float(test[outcome].mean()),
        train_years=",".join(map(str, sorted(train["year"].unique()))),
        test_years=",".join(map(str, sorted(test["year"].unique()))),
        **metrics,
    )
    return model, p, rep


def fit_all(df: pd.DataFrame, outcome: str):
    model = make_calibrated()
    model.fit(df[FEATURES], df[outcome].astype(int))
    return model


def rolling_temporal_validation(panel: pd.DataFrame, outcome: str, min_train_years: int = 2) -> list[ModelReport]:
    years = sorted(panel["year"].dropna().astype(int).unique())
    reports = []
    for i in range(min_train_years, len(years)):
        test_year = years[i]
        train = panel[panel["year"] < test_year].copy()
        test = panel[panel["year"] == test_year].copy()
        if train.empty or test.empty or train[outcome].nunique() < 2 or test[outcome].nunique() < 2:
            continue
        _, _, rep = fit_out_of_time(train, test, outcome)
        reports.append(rep)
    return reports


def temporal_validate_and_refit(panel: pd.DataFrame, outcome: str):
    if panel.empty:
        raise ValueError(f"No observations for {outcome}")
    rolling = rolling_temporal_validation(panel, outcome, min_train_years=2)
    if not rolling:
        raise ValueError("Insufficient cohort variation for rolling out-of-time validation")
    final = fit_all(panel, outcome)
    return final, rolling[-1], rolling


def score_model(model, df: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(df[FEATURES])[:, 1]


def save_model(model, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(model, f)


def _jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def save_reports(reports: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(reports), indent=2), encoding="utf-8")
