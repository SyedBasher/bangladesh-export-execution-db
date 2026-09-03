# Methodology

## 1. Research objective

Most trade databases answer first-order questions: how much was exported, where demand is large, or which products have high RCA. BEOED separates three analytical layers rather than hiding them inside one score.

**Market layer:** How large, fast-growing and contestable is the destination-product market?

**Capability layer:** How close is the product to Bangladesh's observed export capabilities, and how familiar is the destination?

**Execution layer:** Historically, how often do comparable relationships cross a meaningful entry threshold and persist, and what further firm/constraint evidence would be needed before action?

The distinction matters. A very large market can be attractive in the first sense and implausible for Bangladesh in the second.

## 2. Source backbone

The historical backbone is CEPII BACI 202601, HS2012, 2012–2024. BACI reconciles exporter and importer reports from UN Comtrade and reports value and quantity for positive bilateral HS6 flows. Bangladesh is code 050 in the BACI numeric country coding.

For each year the pipeline derives compact tables: Bangladesh product-destination flows; destination-product market size and supplier structure; Bangladesh product totals and destination breadth; Bangladesh destination totals; and, for the latest year, a country-product matrix used for RCA/complexity calculations.

## 3. Public descriptive variables

### Bangladesh market share

`bd_market_share = Bangladesh exports to destination / destination imports from all suppliers`.

### Market growth

Five-year CAGR of the destination-product market where a valid positive base exists.

### Supplier concentration

HHI is the sum of squared supplier shares. `top_supplier_share` is retained separately.

### Destination familiarity

A percentile-scaled measure of Bangladesh's total merchandise exports to the destination. **Percentiles are computed once across unique destinations**, then merged back to product-market rows. This avoids overweighting destinations that simply contain more qualifying HS6 markets.

### Product experience

A transparent combination of Bangladesh's global export value in the HS6 line and number of destinations served. **Ranks are computed across unique products**, not repeated product-market rows. It measures observed export experience, not physical production capacity.

### Market attractiveness

`50% market-size percentile + 30% market-growth percentile + 20% supplier-openness percentile`.

This is a market-screening variable, **not an export-potential or investment recommendation**.

### Readiness index

`60% product experience + 40% destination familiarity`.

Again, this is descriptive. It does not establish that Bangladesh can manufacture the product competitively.

## 4. v0.2 capability layer

The latest BACI country-product matrix is used to compute Balassa RCA, country/product complexity and Bangladesh product-space density. The public v0.2 screening file exposes the components (`rca_bd`, `density_bd`, `pci`, world product exports) rather than collapsing them into a proprietary-looking black-box score.

Bangladesh product density uses co-export proximity:

`phi_pq = cooccurrence(p,q) / max(ubiquity_p, ubiquity_q)`.

Density is the proximity-weighted share of related products in which Bangladesh has `RCA >= 1`, with self-proximity removed. Exact ECI/PCI ranks should be benchmarked against an independent implementation before external publication.

## 5. Entry model

For cohort year `y`, eligible observations are destination-product markets above the minimum market-size threshold in which Bangladesh remains below the configured entry threshold. Features use information observable at `y`. The outcome is whether Bangladesh crosses the threshold in any of `y+1...y+3`.

Baseline features are log market size, five-year market growth, supplier HHI, top-supplier share, destination familiarity and product experience. The model is a regularised logistic classifier with imputation, standardisation, class weighting and probability calibration.

## 6. Survival model

A new entry at `y` is a relationship below the threshold at `y-1` and at/above it at `y`. The outcome is whether exports remain at/above the threshold at `y+3`.

From v0.1.1, **all survival predictors are measured at `y-1`, before the entry occurs**. This fixes an earlier feature-timing mismatch and makes the conditional survival model suitable for ex-ante scoring of currently unentered markets.

`execution_probability = P(entry within 3 years) × P(survive 3 years | entry)`.

This remains a predictive diagnostic, not a causal probability under a particular intervention.

## 7. Validation

Validation is rolling and out-of-time: models are repeatedly trained on earlier cohorts and tested on the next available cohort. The report includes:

- ROC-AUC;
- precision-recall AUC (important because entry is rare);
- Brier score and constant-prevalence Brier benchmark;
- Brier skill score;
- top-5% precision, lift and event capture;
- calibration intercept/slope and 10-bin expected calibration error;
- event rates and exact train/test cohort years.

Model probabilities should not be communicated externally without reviewing these diagnostics and stability across thresholds/specifications.

## 8. QA gate

Every full build runs `scripts/run_qa.py`. Critical checks include key uniqueness, HS6/destination coverage, ISO3 and name completeness, mojibake detection, arithmetic identities, variable bounds, v0.2 merge coverage and DuckDB portability. The workflow fails if critical checks do not pass. A machine-readable `models/qa_report.json` is included with the artifact.

## 9. Firm capability and constraints

EPB product registration is an observed registry relationship, not proof of current capacity, scale, destination, certification or profitability. Candidate firm matching begins conservatively at related HS4 and is reserved for deeper investigation. Later constraints may add tariff disadvantage, logistics, certification/NTM intensity, machinery, input structure, financing and client-supplied firm data.
