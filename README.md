# Bangladesh Export Opportunity & Execution Database (BEOED)

> **QA status (v0.1.3):** The public screening layer now requires multi-year export evidence before calling a product established/emerging, adds import-dominance diagnostics, and separates downstream manufacturing adjacency from process-industry, advanced-technology, recycling, and endowment-linked cases. This is still a research/QA build, not a public opportunity ranking.


BEOED is a research data product designed to move beyond **"where is export demand?"** toward the harder questions **"is a product-market relationship close to Bangladesh's observed capabilities, how often do comparable relationships enter and persist, which firms appear related to the capability, what may be blocking execution, and how much domestic value could be captured?"**

## Current status

The repository is in **QA / pre-release development**. The full BACI production pipeline has been run successfully, but the outputs should not yet be described as a public ranking of Bangladesh export opportunities. The build contains explicit QA gates and separates descriptive screening variables from private predictive execution variables.

| Layer | Grain | Status |
|---|---|---|
| v0.1 trade/execution core | latest HS6 × destination, with historical model panels | populated; QA revision in progress |
| v0.2 complexity/product-space screening | HS6 and HS6 × destination | populated from BACI; public transparent component fields only |
| v0.3 firm capability registry | firm × observed product | seed populated: 28 firms / 104 observed links |
| v0.4 value capture | sector prior × product-market | engine/template complete; requires documented source priors |

## What is differentiated

BEOED does **not** claim that a generic export-potential score is proprietary. ITC and other platforms already provide sophisticated export-potential analytics. BEOED's intended additional layer is execution:

`market screen -> capability proximity -> entry probability -> persistence -> observable constraint signatures -> candidate firm capability -> value capture`

The public files expose transparent descriptive components. Entry, persistence, durable-entry, firm-match and later constraint outputs remain research/commissioned layers unless explicitly released.

## Key interpretation rule

`market_attractiveness` is **not** an export-opportunity ranking. A large, fast-growing, contestable foreign market can score highly even when Bangladesh has little plausible production capability. The v0.2 product-space fields (`density_bd`, `rca_bd`, `pci`) are therefore kept separate rather than collapsed into a black-box public score.

## Build

```bash
pip install -r requirements.txt
python scripts/build_all.py     # v0.1 trade core + private entry/persistence models
python scripts/build_v02.py     # BACI RCA/ECI/PCI/density + transparent public screening file
python scripts/build_v03.py     # firm registry + private candidate firm matches
python scripts/build_v04.py     # only after documented value-capture priors are supplied
python scripts/run_qa.py        # release QA gate
python scripts/write_manifest.py
```

The automated GitHub workflow is `.github/workflows/full_build.yml`.

## Data provenance

Core trade data: CEPII BACI 202601, HS2012, 2012–2024. BACI reconciles exporter/importer reports from UN Comtrade. Firm seed data: Bangladesh Export Promotion Bureau public Exporter Database, retrieved 3 September 2026. Public firm outputs omit personal contact information.

## Model interpretation

The entry model asks whether a currently sub-threshold product-market relationship crosses the configured threshold within three years. The persistence model is conditional on entry and, from v0.1.1 onward, uses **pre-entry features measured at y-1**. Both are predictive diagnostics, not causal estimates or investment recommendations. Validation reports ROC-AUC, PR-AUC, Brier skill, lift and calibration diagnostics using rolling out-of-time cohorts.

See `docs/methodology.md`, `docs/data_dictionary.md`, `models/qa_report.json` (after a full build), and `release_manifest.json` before use.
