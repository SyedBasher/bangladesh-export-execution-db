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

`market_attractiveness` ranks destination-product market conditions; it does not by itself measure whether Bangladesh can execute. `readiness_index` is closer to existing trade experience but remains descriptive. Use v0.2 capability fields and, for commissioned/internal work, the validated entry/survival and firm/constraint layers.
