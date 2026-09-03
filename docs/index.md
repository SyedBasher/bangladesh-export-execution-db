# Bangladesh Export Opportunity & Execution Database (BEOED)

BEOED is a versioned research data product for moving from **export opportunity** to **execution evidence**.

## Current build
- v0.1: full HS6 x destination trade/execution pipeline, including out-of-time entry and persistence models.
- v0.2: internally replicated RCA/ECI/PCI and Bangladesh product-space density; optional tariff/gravity adapters.
- v0.3: **populated seed: 28 EPB firms and 104 observed firm-product links**.
- v0.4: domestic-value-capture engine and documented-source template; no unsupported priors are filled.

## Start here
1. Read the companion methodology/navigation guide.
2. Use the Excel firm registry explorer for the v0.3 seed.
3. Run the full GitHub workflow to populate v0.1/v0.2 from CEPII BACI 202601.
4. Treat private probabilities and candidate firm matches as research diagnostics, not recommendations.

## Commercial boundary
The public layer demonstrates provenance and transparent diagnostics. Historical entry/persistence probabilities, candidate firm matching, constraint diagnosis, scenario analysis and client-specific execution layers remain private/commissioned.

See [Build status](../BUILD_STATUS.md), [methodology](methodology.md), [build notes](v01_v04_build_notes.md), and [commercial boundary](commercial_boundary.md).
