# BEOED methodology — pre-release v0.1.2

## 1. Research objective

Most trade databases answer first-order questions: how much was exported, where demand is large, or which products have high RCA. BEOED deliberately separates three analytical layers rather than hiding them inside one score.

**Market layer:** How large, fast-growing and contestable is the destination-product market?

**Capability layer:** What evidence exists that Bangladesh already exports the product, exports related products, or has a nearby product-space capability?

**Execution layer:** Historically, how often do comparable product-market relationships cross a meaningful entry threshold and persist, and what firm/constraint evidence is still required before action?

A large market can therefore be attractive on the first dimension while remaining implausible on the second or third.

## 2. Source backbone

The historical backbone is CEPII BACI 202601, HS2012, 2012–2024. BACI reconciles exporter and importer reports from UN Comtrade and reports value and quantity for positive bilateral HS6 flows. Bangladesh is code 050 in the BACI numeric country coding.

For each year the pipeline derives compact tables for Bangladesh product-destination flows, destination-product market size and supplier structure, Bangladesh product totals/destination breadth, and Bangladesh destination totals. The latest year also retains the global country-product matrix needed for RCA and complexity calculations.

## 3. Public market and trade-history variables

### Bangladesh market share

`bd_market_share = Bangladesh exports to destination / destination imports from all suppliers`.

### Market growth and growth reliability

`market_cagr_5y` reports the five-year CAGR where a positive historical base exists. Very large percentage growth from a de minimis base can be economically misleading, so `market_growth_status` distinguishes:

- `stable_base`: five-year base at least USD 1 million;
- `small_base`: positive base below USD 1 million;
- `missing_base`: no usable base.

The raw CAGR remains visible, but `market_attractiveness` gives `small_base` and `missing_base` observations a neutral growth contribution rather than rewarding an explosive percentage increase from a tiny denominator.

### Supplier concentration

`supplier_hhi` is the sum of squared supplier shares in the destination-product market. `top_supplier_share` is retained separately.

### Destination familiarity

`destination_familiarity` is a percentile-scaled measure of Bangladesh's total merchandise exports to the destination. Percentiles are computed once across unique destinations and then merged back to product-market rows, so countries containing more qualifying HS6 markets do not receive extra statistical weight.

### Product experience

`product_experience` combines Bangladesh's global export value in the HS6 line and the number of destinations served. Ranks are computed across unique products rather than repeated product-market rows. Absolute `bd_product_exports_usd` and `bd_product_destinations` are also retained because a high percentile among many very small products does not by itself indicate substantial capability.

### Market attractiveness

`market_attractiveness = 50% market-size percentile + 30% reliable-growth percentile + 20% supplier-openness percentile`.

This is a **market-side screening measure**, not an export-potential score or investment recommendation.

### Trade familiarity

`trade_familiarity_index = 60% product experience + 40% destination familiarity`.

The previous label `readiness_index` has been retired. Observed trade history is useful evidence, but it does not establish machinery, certification, input availability, firm scale, finance, buyer qualification, or production economics.

## 4. v0.2 capability layer

The latest BACI country-product matrix is used to compute Balassa RCA, country/product complexity and Bangladesh product-space density. BEOED exposes the components rather than collapsing them into a proprietary-looking black-box opportunity score.

Bangladesh product-space density uses co-export proximity:

`phi_pq = cooccurrence(p,q) / max(ubiquity_p, ubiquity_q)`.

Density is the proximity-weighted share of related products in which Bangladesh has `RCA >= 1`, with self-proximity removed. Exact ECI/PCI levels/ranks remain an internal replication until benchmarked against an independent implementation.

### Capability status

The public screening layer uses transparent rules:

- `established_rca`: Bangladesh RCA >= 1;
- `emerging_observed`: RCA < 1 but Bangladesh exports at least USD 1 million globally;
- `adjacent_observed`: smaller observed exports (at least USD 100,000), RCA < 1 and product-space density percentile >= 0.75;
- `latent_adjacent`: less than USD 100,000 of observed exports but density percentile >= 0.75;
- `distant_or_unobserved`: none of the above.

`latent_adjacent` is **not** an opportunity classification. It means only that related export capabilities are present in the co-export network.

### Product groups and endowment caution

A coarse HS-chapter `product_group` separates manufacturing-like products from agriculture/food, minerals/fuels, precious metals/stones, restricted categories and other non-manufacturing tracks. This prevents a high product-space density for cocoa beans, ores, gold or another endowment-dependent product from being presented in the same way as adjacency in electrical equipment, fabricated metals or other manufacturing.

### Screening classes

`screening_class` organizes product-market rows into descriptive questions:

- `established_product_market_gap`: Bangladesh has RCA>=1 but less than 1% of the destination-product market;
- `emerging_product_market_gap`: Bangladesh has at least USD 1 million of observed product exports, RCA<1 and less than 0.5% destination share;
- `adjacent_manufacturing_requires_validation`: high adjacency in a manufacturing product without established RCA; firm/technology/standards/input feasibility must be checked;
- `latent_endowment_or_other_requires_validation`: high adjacency in a non-manufacturing or endowment-dependent track; independent feasibility evidence is required;
- `existing_strength_destination`: RCA>=1 and at least 1% destination share;
- `exploratory`: none of the above.

`complexity_upgrade_flag` identifies non-established manufacturing products with at least median PCI and emerging/adjacent capability evidence. It is a research filter, not a recommendation.

## 5. Entry model

For cohort year `y`, eligible observations are destination-product markets above the minimum market-size threshold in which Bangladesh remains below the configured entry threshold. Features are observed at `y`. The outcome is whether Bangladesh crosses the threshold in any of `y+1...y+3`.

The private model uses market size, reliably measured five-year market growth, supplier HHI, top-supplier share, destination familiarity, product experience, and absolute Bangladesh product/destination trade-scale variables. The baseline classifier is regularised logistic regression with imputation, standardisation, class weighting and probability calibration.

## 6. Persistence model and durable-entry score

A new entry at `y` is a relationship below the threshold at `y-1` and at/above it at `y`. All persistence predictors are measured at `y-1`, before the entry occurs. The outcome is whether exports are at or above the threshold in `y+3`.

Because intervening years may be intermittent, the model is named `persistence_probability_3y`, not survival probability.

`durable_entry_score = P(entry within 3 years) × P(active at y+3 | entry)`.

This multiplication is retained only as a **composite ranking diagnostic**. It is not described as one fixed-horizon calibrated probability because the entry itself may occur at different points within the three-year entry window.

## 7. Validation

Validation is rolling and out-of-time: models are repeatedly trained on earlier cohorts and tested on the next available cohort. The report includes:

- ROC-AUC;
- precision-recall AUC, important because entry is rare;
- Brier score and constant-prevalence Brier benchmark;
- Brier skill score;
- top-5% precision, lift and event capture;
- calibration intercept/slope and 10-bin expected calibration error;
- event rates and exact train/test cohort years.

The QA gate fails if the latest entry AUC falls below 0.80, the latest persistence AUC below 0.60, or either model has non-positive Brier skill. Calibration/lift thresholds generate warnings. Private probability fields should not be communicated externally without reviewing the complete validation report.

## 8. QA gate

Every full build runs `scripts/run_qa.py`. Critical checks include key uniqueness, HS6/destination coverage, ISO3 validity, names and mojibake, market-share arithmetic, variable bounds, minimum market threshold, v0.2 merge/classification coverage, DuckDB portability and minimum predictive performance.

Missing ISO3 is not automatically imputed for BACI aggregate/non-ISO destinations. The QA report lists the affected destinations explicitly.

The workflow fails if critical checks do not pass. A machine-readable `models/qa_report.json` is included with every artifact.

## 9. Firm capability and constraints

EPB product registration is an observed registry relationship, not proof of current capacity, scale, destination, certification or profitability. Candidate firm matching therefore starts conservatively and is reserved for deeper investigation.

Later execution layers may add tariff disadvantage, logistics, certification/NTM intensity, machinery, input structure, financing, domestic-value capture and client-supplied firm information. A product-space signal becomes actionable only after these execution constraints are investigated.
