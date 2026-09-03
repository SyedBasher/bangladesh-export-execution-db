# BEOED v0.1.3 capability-evidence patch

## Why this revision was needed

The v0.1.2 QA build passed its technical checks and materially improved model performance, but the economic-content audit found two remaining risks:

1. a single latest-year export value could be mistaken for durable productive capability; and
2. the chapter-level manufacturing screen treated very different production technologies as if they were comparable. For example, fabricated steel structures and electrical conductors appeared in the same adjacency screen as refined copper, semi-finished steel, primary polymers, fertilizer, and scrap streams.

These are interpretation problems, not BACI arithmetic problems.

## Changes

- Adds Bangladesh HS6 imports and number of import origins to the annual product table.
- Adds five-year export-persistence fields: positive years, years >= USD 100k, years >= USD 1m, five-year mean, and five-year maximum.
- Adds net-export and log export/import diagnostics.
- Adds `capability_evidence_status`: persistent_large, persistent_small, recent_large, recent_small, minimal_or_none.
- Adds `import_dominance_flag`; this is not proof of re-exporting.
- Adds `feasibility_archetype`: downstream manufacturing, process/capital-intensive, advanced technology, recycling/scrap, agri-food/endowment-linked, other, and excluded regulated category.
- Makes `established_product_market_gap` require persistent export evidence.
- Makes `emerging_product_market_gap` require persistent-large export evidence and no import-dominance flag.
- Adds `recent_export_signal_requires_validation` for large but non-persistent export observations.
- Splits adjacency into downstream manufacturing, process industry, advanced technology, and endowment/recycling/other validation classes.
- Excludes regulated categories from opportunity-style screening.
- Adds QA checks so persistent-evidence semantics cannot silently regress.
- Adds separate CSV samples for recent export signals, process-industry validation, and advanced-technology validation.

## What does not change

- `market_attractiveness` remains a descriptive market-condition index, not export potential.
- Product-space density remains a statistical adjacency measure, not proof of technical feasibility.
- Entry and persistence model probabilities remain private/internal.
- No domestic-value-added claim is inferred from the export/import diagnostics.

## After the next full build

Inspect these first:

- `models/qa_report.json`
- `models/validation_report.json`
- `data/public/beoed_established_product_market_gaps_sample.csv`
- `data/public/beoed_emerging_products_sample.csv`
- `data/public/beoed_adjacent_manufacturing_sample.csv`
- `data/public/beoed_recent_export_signals_sample.csv`
- `data/public/beoed_process_industry_validation_sample.csv`
- `data/public/beoed_advanced_technology_validation_sample.csv`
