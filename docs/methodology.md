# Methodology

## 1. Research objective

Most trade databases answer first-order questions: how much was exported, where demand is large, or which products have high RCA. BEOED is designed to add two further layers.

**Second order:** Is the market attractive *conditional on competition, Bangladesh's product experience, destination familiarity, and historical entry behaviour*?

**Third order:** If an opportunity is not being captured, what observable constraint signatures are present, how likely is entry to persist, and what additional firm-specific information would be required before recommending action?

## 2. Source backbone

The initial historical backbone is CEPII BACI 202601, HS2012, 2012-2024. BACI reconciles exporter and importer reports from UN Comtrade and reports value and quantity for positive bilateral HS6 flows. Bangladesh is code 050 in the numeric country coding.

The build pipeline does not retain the entire global BACI row-level file. For each year it derives compact analytical tables: Bangladesh product-destination flows; destination-product market size; supplier HHI and top-supplier share; Bangladesh product experience; and Bangladesh destination familiarity.

## 3. Public descriptive variables

### Bangladesh market share

`bd_market_share = Bangladesh exports to destination / destination imports from all suppliers`.

### Market growth

Five-year CAGR of the destination-product market, where a valid positive base exists.

### Supplier concentration

HHI is the sum of squared supplier shares in the destination-product market. Top-supplier share is retained separately because two markets with the same HHI can have different competitive structures.

### Destination familiarity

A percentile-scaled transformation of Bangladesh's total merchandise exports to the destination. It is a proxy for existing commercial/logistical familiarity, not proof that buyers or distribution channels are transferable across products.

### Product experience

A transparent combination of Bangladesh's global export value in the HS6 line and the number of destinations already served. It measures observed export experience, not production capacity.

### Market attractiveness

A deliberately transparent screening index:

`50% market-size percentile + 30% market-growth percentile + 20% supplier-openness percentile`.

It is **not** an ITC-style export-potential estimate and is intentionally kept separate from the execution model.

### Readiness index

`60% product experience + 40% destination familiarity`.

This is also descriptive. It answers whether the product-market pair looks relatively close to Bangladesh's observed trade experience.

## 4. Entry model

Historical observations are constructed at product-destination-year level when Bangladesh is below an entry threshold (initially US$100,000). The outcome is whether exports cross that threshold within the following three years.

Version 0.1 uses only lagged information available at the decision date: log destination-market size, five-year market growth, supplier concentration, top-supplier share, destination familiarity, and product experience. No future values enter the feature matrix.

The baseline estimator is a regularised logistic model with missing-value imputation, standardisation, class weighting, and probability calibration. Evaluation is strictly out-of-time. Reported metrics include ROC-AUC and Brier score; calibration plots should accompany any external use of the probability field.

## 5. Survival model

Conditional on a new entry, the survival outcome asks whether the relationship remains above a defined activity threshold three years later. Entry and survival are estimated separately because the determinants of starting a trade relationship need not equal the determinants of sustaining it.

`execution_probability = P(entry within 3 years) × P(survive 3 years | entry)`.

This is a predictive diagnostic, not a causal probability of success under a particular policy intervention.

## 6. Diagnostic flags

Initial flags include declining market, high supplier concentration, low destination familiarity, low product experience, and already-high Bangladesh share. Later releases can add tariff disadvantage, distance/trade-cost exposure, certification/NTM intensity, unit-value position, and firm-specific capability gaps.

Flags are observable symptoms. They must not be described as proven reasons for non-entry without additional identification or primary evidence.

## 7. Planned extensions

- preferential and MFN tariff gaps relative to major competitors;
- CEPII Gravity/ESCAP trade costs;
- HS6 product-space density and PCI;
- quantity/unit-value diagnostics where BACI quantity units are economically interpretable;
- firm-capability registry assembled from EPB, associations, certification registries, company disclosures and client-supplied data;
- domestic-value-capture proxies using input-output/TiVA and Bangladesh sector data;
- vintage-preserving monthly/annual updates for real-time monitoring.

## 8. Validation philosophy

No composite index should be trusted merely because it looks plausible. Each release should include: source-vintage checks, row-count and uniqueness checks, reconciliation against independent published totals, out-of-time model validation, stability across thresholds, missing-data flags, and a changelog describing revisions.
