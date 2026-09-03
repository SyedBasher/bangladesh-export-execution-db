from __future__ import annotations
import numpy as np
import pandas as pd


def _hs2(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype("string").str.zfill(6).str[:2], errors="coerce").astype("Int64")


def add_product_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Add broad HS product groups used only to separate screening questions.

    The grouping is intentionally coarse. It prevents a product-space adjacency in a
    raw commodity or extractive product from being presented in the same way as an
    adjacent manufacturing capability. It is not an industrial classification.
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
        "arms_ammunition",
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


def add_capability_screen(df: pd.DataFrame) -> pd.DataFrame:
    """Create transparent capability/screening classes; no black-box opportunity score.

    Rules deliberately separate observed export capability from product-space adjacency.
    ``latent_adjacent`` means only that related products are present in Bangladesh's RCA
    basket; it *requires feasibility validation* and is never labelled an opportunity.
    """
    out = add_product_groups(df)
    rca = pd.to_numeric(out.get("rca_bd"), errors="coerce").fillna(0)
    density_pct = pd.to_numeric(out.get("density_bd_percentile"), errors="coerce").fillna(0)
    product_exports = pd.to_numeric(out.get("bd_exports_usd"), errors="coerce").fillna(0)
    share = pd.to_numeric(out.get("bd_market_share"), errors="coerce").fillna(0)
    pci_pct = pd.to_numeric(out.get("pci_percentile"), errors="coerce")

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

    out["complexity_upgrade_flag"] = (
        out["manufacturing_screen"]
        & out["capability_status"].isin(["emerging_observed", "adjacent_observed", "latent_adjacent"])
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
    out["screening_class"] = np.select(
        [
            (rca >= 1.0) & (share >= 0.01),
            (rca >= 1.0) & (share < 0.01),
            cap.eq("emerging_observed") & (share < 0.005),
            cap.isin(["adjacent_observed", "latent_adjacent"]) & out["manufacturing_screen"] & (share < 0.001),
            cap.isin(["adjacent_observed", "latent_adjacent"]) & ~out["manufacturing_screen"] & (share < 0.001),
        ],
        [
            "existing_strength_destination",
            "established_product_market_gap",
            "emerging_product_market_gap",
            "adjacent_manufacturing_requires_validation",
            "latent_endowment_or_other_requires_validation",
        ],
        default="exploratory",
    )
    return out


def sample_priority(df: pd.DataFrame) -> pd.Series:
    """Internal sort key for examples; lower is shown first. Not an opportunity score."""
    order = {
        "established_product_market_gap": 1,
        "emerging_product_market_gap": 2,
        "adjacent_manufacturing_requires_validation": 3,
        "existing_strength_destination": 4,
        "latent_endowment_or_other_requires_validation": 5,
        "exploratory": 6,
    }
    return df["screening_class"].map(order).fillna(99).astype(int)
