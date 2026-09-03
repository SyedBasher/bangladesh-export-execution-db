# Data dictionary

The canonical variable registry is `config/variables.yml`. Every field is tagged by layer, public status, definition and source.

## Main release tables

| Table/file | Grain | Purpose |
|---|---|---|
| `beoed_public_latest.*` | 2024 HS6 × destination | Transparent trade/market screening layer |
| `beoed_public_screening_v02.*` | 2024 HS6 × destination | Public trade screen plus RCA/PCI/product-space components |
| `beoed_public.duckdb` | portable database | Physical `public_latest` and `public_screening_v02` tables |
| `product_space_latest.parquet` | HS6 | PCI, Bangladesh density/RCA and world product exports |
| `eci_latest.parquet` | economy | internally replicated ECI and diversity |
| `firm_registry_seed.*` | firm | public EPB seed registry, no personal contacts |
| `firm_product_links_seed.*` | firm × observed code | observed EPB firm-product registrations |
| `validation_report.json` | model/cohort | predictive validation diagnostics |
| `qa_report.json` | release | automated release-quality checks |

## Important interpretation

`market_attractiveness` ranks destination-product market conditions; it does not by itself measure whether Bangladesh can execute. `trade_familiarity_index` is closer to existing trade experience but remains descriptive. Use v0.2 capability fields and, for commissioned/internal work, the validated entry/persistence and firm/constraint layers.

### Screening classes added in v0.1.2

- `established_product_market_gap`: Bangladesh has RCA>=1 in the product but less than 1% share in this destination-product market.
- `emerging_product_market_gap`: Bangladesh has at least USD 1 million of observed product exports but RCA<1 and less than 0.5% destination-market share.
- `adjacent_manufacturing_requires_validation`: product-space adjacency is high for a manufacturing product, but observed capability is not yet established; feasibility validation is required.
- `latent_endowment_or_other_requires_validation`: high product-space adjacency occurs in an agriculture, extractive, precious-metal, restricted, or other non-manufacturing track; it must not be interpreted as an executable opportunity without independent endowment/capability evidence.
- `existing_strength_destination`: Bangladesh already has RCA>=1 and at least 1% of the destination-product market.
- `exploratory`: none of the above.
