from __future__ import annotations
from pathlib import Path
import json
import re
import duckdb
import numpy as np
import pandas as pd

BAD_TEXT_RE = re.compile(r"Ã|Â|â€|ðŸ")


def _rate(s: pd.Series) -> float:
    return float(s.mean()) if len(s) else 0.0


def _bounds_fail(s: pd.Series, lo: float, hi: float, tol: float = 1e-9) -> int:
    x = pd.to_numeric(s, errors="coerce")
    return int(((x < lo-tol) | (x > hi+tol)).sum())


def _check_model_quality(validation: dict | None, failures: list[str], warnings: list[str]) -> dict | None:
    if not validation:
        warnings.append("validation report missing")
        return None
    out = {}
    specs = {
        "entry_probability_3y": {"min_auc":0.80, "min_lift":5.0, "slope":(0.70,1.30)},
        "persistence_probability_3y": {"min_auc":0.60, "min_lift":1.20, "slope":(0.60,1.50)},
    }
    for key, rule in specs.items():
        block = validation.get(key)
        if not block:
            warnings.append(f"{key} validation block missing")
            continue
        latest = block.get("latest_holdout", {})
        out[key] = {
            "auc": latest.get("auc"),
            "pr_auc": latest.get("pr_auc"),
            "brier_skill": latest.get("brier_skill"),
            "top_5pct_lift": latest.get("top_5pct_lift"),
            "calibration_intercept": latest.get("calibration_intercept"),
            "calibration_slope": latest.get("calibration_slope"),
            "ece_10bin": latest.get("ece_10bin"),
        }
        auc = latest.get("auc")
        skill = latest.get("brier_skill")
        lift = latest.get("top_5pct_lift")
        cint = latest.get("calibration_intercept")
        slope = latest.get("calibration_slope")
        if auc is None or auc < rule["min_auc"]:
            failures.append(f"{key} latest holdout AUC below {rule['min_auc']:.2f}")
        if skill is None or skill <= 0:
            failures.append(f"{key} has non-positive Brier skill on latest holdout")
        if lift is not None and lift < rule["min_lift"]:
            warnings.append(f"{key} top-5% lift {lift:.2f} is below preferred {rule['min_lift']:.2f}")
        if cint is not None and abs(cint) > 0.50:
            warnings.append(f"{key} calibration intercept {cint:.2f} indicates material level miscalibration")
        if slope is not None and not (rule["slope"][0] <= slope <= rule["slope"][1]):
            warnings.append(f"{key} calibration slope {slope:.2f} lies outside preferred range {rule['slope']}")
    return out


def audit_release(
    public_path: Path,
    v02_path: Path | None,
    duckdb_path: Path,
    annual_bd_flows_path: Path | None,
    eci_path: Path | None,
    validation_path: Path | None,
    min_market_usd: float,
) -> dict:
    pub = pd.read_parquet(public_path)
    failures: list[str] = []
    warnings: list[str] = []

    keys = ["year","hs6","destination_code"]
    duplicate_rows = int(pub.duplicated(keys).sum())
    iso_blank = pub["iso3"].isna() | pub["iso3"].astype("string").str.strip().eq("") if "iso3" in pub else pd.Series(True,index=pub.index)
    iso_missing = _rate(iso_blank)
    invalid_iso = int((~pub["iso3"].astype("string").fillna("").str.match(r"^(|[A-Z]{3})$")).sum()) if "iso3" in pub else len(pub)
    dest_missing = _rate(pub["destination_name"].isna()) if "destination_name" in pub else 1.0
    product_missing = _rate(pub["product_name"].isna()) if "product_name" in pub else 1.0
    bad_text = 0
    for c in ["destination_name","product_name"]:
        if c in pub:
            bad_text += int(pub[c].astype("string").fillna("").str.contains(BAD_TEXT_RE).sum())

    share_identity = np.nanmax(np.abs(
        pd.to_numeric(pub["bd_market_share"], errors="coerce").to_numpy(float)
        - (
            pd.to_numeric(pub["bd_exports_to_destination_usd"], errors="coerce").to_numpy(float)
            / pd.to_numeric(pub["destination_market_usd"], errors="coerce").replace(0,np.nan).to_numpy(float)
        )
    ))

    missing_iso_destinations = []
    if "destination_name" in pub and iso_blank.any():
        m = (pub.loc[iso_blank, ["destination_code","destination_name"]]
             .value_counts(dropna=False).reset_index(name="row_count")
             .sort_values("row_count",ascending=False).head(25))
        missing_iso_destinations = m.to_dict("records")

    growth_counts = pub["market_growth_status"].value_counts(dropna=False).to_dict() if "market_growth_status" in pub else {}
    summary = {
        "row_count": int(len(pub)),
        "years": sorted(map(int, pd.Series(pub["year"].dropna().unique()).tolist())),
        "hs6_count": int(pub["hs6"].astype(str).nunique()),
        "destination_count": int(pub["destination_code"].nunique()),
        "duplicate_key_rows": duplicate_rows,
        "iso3_missing_rate": iso_missing,
        "iso3_invalid_count": invalid_iso,
        "iso3_missing_destinations": missing_iso_destinations,
        "destination_name_missing_rate": dest_missing,
        "product_name_missing_rate": product_missing,
        "mojibake_row_cells": bad_text,
        "share_identity_max_abs_error": float(share_identity) if np.isfinite(share_identity) else None,
        "zero_bd_export_share": float((pd.to_numeric(pub["bd_exports_to_destination_usd"],errors="coerce").fillna(0)==0).mean()),
        "screening_bd_exports_usd": float(pd.to_numeric(pub["bd_exports_to_destination_usd"],errors="coerce").fillna(0).sum()),
        "market_growth_status_counts": {str(k):int(v) for k,v in growth_counts.items()},
    }

    if annual_bd_flows_path and annual_bd_flows_path.exists():
        annual = pd.read_parquet(annual_bd_flows_path)
        all_bd = float(pd.to_numeric(annual["bd_exports_to_destination_usd"],errors="coerce").fillna(0).sum())
        summary["all_bd_exports_usd"] = all_bd
        summary["screening_export_coverage"] = summary["screening_bd_exports_usd"] / all_bd if all_bd > 0 else None

    if len(pub) < 100_000:
        failures.append("public row count unexpectedly below 100,000")
    if summary["hs6_count"] < 3_000:
        failures.append("HS6 coverage unexpectedly below 3,000 products")
    if summary["destination_count"] < 150:
        failures.append("destination coverage unexpectedly below 150 economies")
    if duplicate_rows:
        failures.append(f"{duplicate_rows} duplicate year-HS6-destination rows")
    if iso_missing > 0.05:
        failures.append(f"ISO3 missing rate {iso_missing:.1%} exceeds 5%")
    elif iso_missing > 0:
        warnings.append("Some BACI destinations have no standard ISO3 code; inspect iso3_missing_destinations rather than imputing one")
    if invalid_iso:
        failures.append(f"{invalid_iso} nonblank ISO3 values are not three uppercase letters")
    if dest_missing > 0.01:
        failures.append(f"destination-name missing rate {dest_missing:.1%} exceeds 1%")
    if product_missing > 0.01:
        failures.append(f"product-name missing rate {product_missing:.1%} exceeds 1%")
    if bad_text:
        failures.append(f"{bad_text} text cells retain common mojibake markers")
    if summary["share_identity_max_abs_error"] is not None and summary["share_identity_max_abs_error"] > 1e-9:
        failures.append("Bangladesh market-share arithmetic identity fails tolerance")

    for col,lo,hi in [
        ("bd_market_share",0,1), ("supplier_hhi",0,1), ("top_supplier_share",0,1),
        ("destination_familiarity",0,1), ("product_experience",0,1),
        ("market_attractiveness",0,100), ("trade_familiarity_index",0,100),
    ]:
        if col not in pub:
            failures.append(f"required public field missing: {col}")
            continue
        n = _bounds_fail(pub[col],lo,hi)
        if n:
            failures.append(f"{col}: {n} values outside [{lo},{hi}]")
    below_market = int((pd.to_numeric(pub["destination_market_usd"],errors="coerce") < min_market_usd-1).sum())
    if below_market:
        failures.append(f"{below_market} rows below configured destination-product market threshold")

    v02_summary = None
    if v02_path and v02_path.exists():
        v = pd.read_parquet(v02_path)
        class_counts = v["screening_class"].value_counts(dropna=False).to_dict() if "screening_class" in v else {}
        capability_counts = v["capability_status"].value_counts(dropna=False).to_dict() if "capability_status" in v else {}
        v02_summary = {
            "row_count": int(len(v)),
            "pci_coverage": float(v["pci"].notna().mean()) if "pci" in v else 0.0,
            "density_bd_coverage": float(v["density_bd"].notna().mean()) if "density_bd" in v else 0.0,
            "rca_bd_coverage": float(v["rca_bd"].notna().mean()) if "rca_bd" in v else 0.0,
            "screening_class_counts": {str(k):int(val) for k,val in class_counts.items()},
            "capability_status_counts": {str(k):int(val) for k,val in capability_counts.items()},
            "complexity_upgrade_rows": int(v["complexity_upgrade_flag"].fillna(False).sum()) if "complexity_upgrade_flag" in v else 0,
        }
        if len(v) != len(pub):
            failures.append("v0.2 public screening row count differs from v0.1 public snapshot")
        for c in ["pci_coverage","density_bd_coverage","rca_bd_coverage"]:
            if v02_summary[c] < 0.95:
                failures.append(f"v0.2 {c} below 95%")
        if "density_bd" in v and _bounds_fail(v["density_bd"],0,1):
            failures.append("density_bd has values outside [0,1]")
        for col in ["capability_status","screening_class","product_group","market_condition"]:
            if col not in v or v[col].isna().any():
                failures.append(f"v0.2 classification field missing/incomplete: {col}")

    duckdb_summary = {"exists": duckdb_path.exists()}
    if duckdb_path.exists():
        con = duckdb.connect(str(duckdb_path), read_only=True)
        try:
            table_count = int(con.execute("SELECT COUNT(*) FROM public_latest").fetchone()[0])
            physical = int(con.execute("SELECT COUNT(*) FROM duckdb_tables() WHERE table_name='public_latest'").fetchone()[0])
            views = int(con.execute("SELECT COUNT(*) FROM duckdb_views() WHERE view_name='public_latest'").fetchone()[0])
            v02_table = int(con.execute("SELECT COUNT(*) FROM duckdb_tables() WHERE table_name='public_screening_v02'").fetchone()[0])
        finally:
            con.close()
        duckdb_summary.update({"public_latest_rows":table_count,"physical_table":bool(physical),"view_count":views,"v02_physical_table":bool(v02_table)})
        if table_count != len(pub):
            failures.append("DuckDB public_latest row count differs from Parquet")
        if not physical or views:
            failures.append("DuckDB public_latest is not a self-contained physical table")
        if v02_path and v02_path.exists() and not v02_table:
            failures.append("DuckDB public_screening_v02 physical table missing")
    else:
        failures.append("DuckDB output missing")

    eci_summary = None
    if eci_path and eci_path.exists():
        e = pd.read_parquet(eci_path)
        eci_summary = {
            "country_count": int(len(e)),
            "eci_missing_rate": float(e["eci"].isna().mean()) if "eci" in e else 1.0,
        }
        if len(e) < 150:
            warnings.append("ECI table contains fewer than 150 economies; inspect country coverage")

    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path and validation_path.exists() else None
    model_quality = _check_model_quality(validation, failures, warnings)

    return {
        "qa_pass": len(failures) == 0,
        "critical_failures": failures,
        "warnings": warnings,
        "public_summary": summary,
        "v02_summary": v02_summary,
        "duckdb_summary": duckdb_summary,
        "eci_summary": eci_summary,
        "model_quality_summary": model_quality,
        "validation": validation,
    }


def write_qa_report(report: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
