# Bangladesh Export Opportunity & Execution Database (BEOED)

BEOED is a research data product designed to move beyond the question **"where is export demand?"** toward the harder questions **"can Bangladesh execute, which relationships persist, which firms appear related to the capability, what is blocking execution, and how much domestic value could be captured?"**

## Architecture

| Layer | Grain | Status |
|---|---|---|
| v0.1 trade/execution core | year x HS6 x destination | production pipeline complete; populate on GitHub runner |
| v0.2 complexity/market access | HS6 and HS6 x destination | BACI complexity/product-space engine complete; tariff/gravity adapters ready |
| v0.3 firm capability registry | firm x observed product | **seed populated: 28 firms / 104 links** |
| v0.4 value capture | HS/industry prior x product-market | engine/template complete; requires documented source priors |

## What is differentiated
BEOED does **not** claim that a generic export-potential score is proprietary. ITC and other platforms already do that well. The intended proprietary layer is execution:

`opportunity -> entry probability -> persistence -> observable constraint signatures -> candidate firm capability -> value capture`

Model outputs are predictive diagnostics, not causal estimates or investment recommendations.

## Build

```bash
pip install -r requirements.txt
python scripts/build_all.py     # v0.1, including private entry/survival models
python scripts/build_v02.py     # BACI complexity/product-space + optional market-access sources
python scripts/build_v03.py     # firm registry + private candidate firm matches
python scripts/build_v04.py     # only after documented value-capture priors are supplied
```

The full automated GitHub build is in `.github/workflows/full_build.yml`.

## Data provenance
Core trade data: CEPII BACI 202601, HS2012, 2012–2024. CEPII distributes BACI under the Etalab Open Licence 2.0 and requests source attribution. Firm seed data: Bangladesh Export Promotion Bureau public Exporter Database, retrieved 3 September 2026. Public firm outputs omit personal contact information.

## Interpretation guardrail
An EPB product registration is an **observed relationship in the registry**. It is not proof of current plant capacity, quantity exported, destination served, technical certification, profitability, or ability to manufacture a related product. Candidate firm matches retain that distinction explicitly.

See `BUILD_STATUS.md`, `docs/methodology.md`, and the companion guide before use.
