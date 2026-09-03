from __future__ import annotations
import re
import numpy as np
import pandas as pd


def _hs2(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype("string").str.zfill(6).str[:2], errors="coerce").astype("Int64")


def _hs4(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype("string").str.zfill(6).str[:4], errors="coerce").astype("Int64")


def add_product_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Add broad HS product groups used only to separate screening questions.

    The groups are intentionally coarse. They are not an industrial classification and
    should not be read as evidence that products within a chapter use the same technology.
    """
    out = df.copy()
    h2 = _hs2(out["hs6"])
    conditions = [
        h2.between(1, 24),
        h2.between(25, 27),
        h2.between(28, 40),
        h2.between(41, 49),
        h2.between(50, 67),
        h2.between(68, 70),
        h2.eq(71),
        h2.between(72, 83),
        h2.between(84, 85),
        h2.between(86, 89),
        h2.between(90, 92),
        h2.eq(93),
        h2.between(94, 96),
        h2.eq(97),
    ]
    choices = [
        "agriculture_food",
        "minerals_fuels",
        "chemicals_plastics_rubber",
        "leather_wood_paper",
        "textiles_footwear",
        "stone_glass",
        "precious_metals_stones",
        "metals_articles",
        "machinery_electrical",
        "transport_equipment",
        "instruments_misc",
        "regulated_excluded",
        "other_manufactures",
        "art_antiques",
    ]
    out["product_group"] = np.select(conditions, choices, default="special_other")
    manufacturing_groups = {
        "chemicals_plastics_rubber", "leather_wood_paper", "textiles_footwear",
        "stone_glass", "metals_articles", "machinery_electrical",
        "transport_equipment", "instruments_misc", "other_manufactures",
    }
    out["manufacturing_screen"] = out["product_group"].isin(manufacturing_groups)
    return out


def add_feasibility_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    """Add a coarse production/feasibility archetype for interpretation.

    This is a *diagnostic*, not a feasibility model. Its purpose is to prevent product-space
    proximity from making upstream process industries, scrap streams, advanced technology,
    and ordinary downstream manufacturing look economically equivalent.
    """
    out = add_product_groups(df)
    h2 = _hs2(out["hs6"])
    h4 = _hs4(out["hs6"])
    name = out.get("product_name", pd.Series("", index=out.index)).astype("string").fillna("").str.lower()

    recycling = name.str.contains(r"\b(?:waste|scrap|spent)\b", regex=True)
    regulated = h2.eq(93)
    # Upstream/basic production that generally requires substantial feedstock, energy,
    # refining/smelting or continuous-process capacity. The list is intentionally coarse.
    process = (
        h2.between(25, 29)
        | h4.between(3102, 3105)
        | h4.between(3901, 3914)
        | h2.eq(72)
        | h4.between(7401, 7405)
        | h4.between(7501, 7504)
        | h4.isin([7601, 7801, 7901, 8001])
    ) & ~recycling
    advanced = (
        h4.isin([8541, 8542])
        | h4.isin([8802, 8803])
    ) & ~recycling & ~process
    agri_food = h2.between(1, 24)
    downstream = out["manufacturing_screen"] & ~process & ~recycling & ~advanced & ~regulated

    out["feasibility_archetype"] = np.select(
        [regulated, recycling, process, advanced, downstream, agri_food],
        [
            "regulated_excluded",
            "recycling_scrap",
            "process_capital_intensive",
            "advanced_technology_requires_validation",
            "downstream_manufacturing",
            "agri_food_endowment_or_processing",
        ],
        default="other_or_endowment_dependent",
    )
    out["commercial_screen_exclusion"] = np.where(regulated, "regulated_excluded", "none")
    return out


def add_capability_evidence(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize how persistent Bangladesh's observed product exports are.

    Current-year exports can reflect a one-off shipment, a re-export, or an unstable trade
    relationship. This categorical layer therefore uses the preceding five-year export
    history to distinguish persistent capability evidence from recent/volatile signals.
    """
    out = df.copy()
    cur = pd.to_numeric(out.get("bd_exports_usd", out.get("bd_product_exports_usd")), errors="coerce").fillna(0)
    y100 = pd.to_numeric(out.get("bd_product_years_ge_100k_5y"), errors="coerce").fillna(0)
    y1m = pd.to_numeric(out.get("bd_product_years_ge_1m_5y"), errors="coerce").fillna(0)

    out["capability_evidence_status"] = np.select(
        [
            (cur >= 1_000_000) & (y1m >= 3),
            (cur >= 100_000) & (y100 >= 3),
            cur >= 1_000_000,
            cur >= 100_000,
        ],
        ["persistent_large", "persistent_small", "recent_large", "recent_small"],
        default="minimal_or_none",
    )
    imports = pd.to_numeric(out.get("bd_product_imports_usd"), errors="coerce").fillna(0)
    out["import_dominance_flag"] = (cur >= 1_000_000) & (imports >= 5_000_000) & (imports >= 5 * cur)
    return out


def add_capability_screen(df: pd.DataFrame) -> pd.DataFrame:
    """Create transparent capability/screening classes; no black-box opportunity score.

    v0.1.3 distinguishes (i) current export scale, (ii) persistence of that evidence,
    (iii) product-space adjacency, and (iv) broad production archetype. Statistical
    adjacency remains a hypothesis for validation rather than proof of feasibility.
    """
    out = add_feasibility_archetypes(df)
    out = add_capability_evidence(out)
    rca = pd.to_numeric(out.get("rca_bd"), errors="coerce").fillna(0)
    density_pct = pd.to_numeric(out.get("density_bd_percentile"), errors="coerce").fillna(0)
    product_exports = pd.to_numeric(out.get("bd_exports_usd", out.get("bd_product_exports_usd")), errors="coerce").fillna(0)
    share = pd.to_numeric(out.get("bd_market_share"), errors="coerce").fillna(0)
    pci_pct = pd.to_numeric(out.get("pci_percentile"), errors="coerce")
    evidence = out["capability_evidence_status"]
    archetype = out["feasibility_archetype"]
    excluded = out["commercial_screen_exclusion"].ne("none")

    out["capability_status"] = np.select(
        [
            rca >= 1.0,
            (rca < 1.0) & (product_exports >= 1_000_000),
            (rca < 1.0) & (product_exports >= 100_000) & (density_pct >= 0.75),
            (rca < 1.0) & (product_exports < 100_000) & (density_pct >= 0.75),
        ],
        ["established_rca", "emerging_observed", "adjacent_observed", "latent_adjacent"],
        default="distant_or_unobserved",
    )

    # High-PCI signals are retained as diagnostics only when they are not import-dominant
    # and are outside the excluded category. A flag is not a recommendation.
    out["complexity_upgrade_flag"] = (
        ~excluded
        & archetype.isin(["downstream_manufacturing", "advanced_technology_requires_validation"])
        & out["capability_status"].isin(["emerging_observed", "adjacent_observed", "latent_adjacent"])
        & ~out["import_dominance_flag"]
        & pci_pct.ge(0.50).fillna(False)
    )

    out["market_condition"] = np.select(
        [
            pd.to_numeric(out["top_supplier_share"], errors="coerce").fillna(1) >= 0.60,
            out.get("market_growth_status", pd.Series("", index=out.index)).eq("stable_base")
                & pd.to_numeric(out["market_cagr_5y"], errors="coerce").lt(0),
            pd.to_numeric(out["destination_market_usd"], errors="coerce").fillna(0) < 50_000_000,
            out.get("market_growth_status", pd.Series("", index=out.index)).eq("stable_base")
                & pd.to_numeric(out["market_cagr_5y"], errors="coerce").ge(0),
        ],
        ["high_supplier_concentration", "declining_market", "smaller_market", "large_stable_or_growing"],
        default="large_growth_base_uncertain",
    )

    cap = out["capability_status"]
    persistent_any = evidence.isin(["persistent_large", "persistent_small"])
    out["screening_class"] = np.select(
        [
            excluded,
            (rca >= 1.0) & persistent_any & (share >= 0.01),
            (rca >= 1.0) & persistent_any & (share < 0.01),
            (rca >= 1.0) & ~persistent_any & (share < 0.01),
            cap.eq("emerging_observed") & evidence.eq("persistent_large") & ~out["import_dominance_flag"] & (share < 0.005),
            cap.eq("emerging_observed") & evidence.eq("recent_large") & (share < 0.005),
            cap.isin(["adjacent_observed", "latent_adjacent"]) & archetype.eq("downstream_manufacturing") & (share < 0.001),
            cap.isin(["adjacent_observed", "latent_adjacent"]) & archetype.eq("advanced_technology_requires_validation") & (share < 0.001),
            cap.isin(["adjacent_observed", "latent_adjacent"]) & archetype.eq("process_capital_intensive") & (share < 0.001),
            cap.isin(["adjacent_observed", "latent_adjacent"]) & archetype.isin(["recycling_scrap", "agri_food_endowment_or_processing", "other_or_endowment_dependent"]) & (share < 0.001),
        ],
        [
            "excluded_regulated_product",
            "existing_strength_destination",
            "established_product_market_gap",
            "rca_signal_requires_validation",
            "emerging_product_market_gap",
            "recent_export_signal_requires_validation",
            "adjacent_downstream_manufacturing_requires_validation",
            "adjacent_advanced_technology_requires_validation",
            "adjacent_process_industry_requires_validation",
            "latent_endowment_recycling_or_other_requires_validation",
        ],
        default="exploratory",
    )
    return out


def sample_priority(df: pd.DataFrame) -> pd.Series:
    """Internal sort key for examples; lower is shown first. Not an opportunity score."""
    order = {
        "established_product_market_gap": 1,
        "emerging_product_market_gap": 2,
        "adjacent_downstream_manufacturing_requires_validation": 3,
        "recent_export_signal_requires_validation": 4,
        "adjacent_advanced_technology_requires_validation": 5,
        "adjacent_process_industry_requires_validation": 6,
        "existing_strength_destination": 7,
        "rca_signal_requires_validation": 8,
        "latent_endowment_recycling_or_other_requires_validation": 9,
        "exploratory": 10,
        "excluded_regulated_product": 99,
    }
    return df["screening_class"].map(order).fillna(98).astype(int)
