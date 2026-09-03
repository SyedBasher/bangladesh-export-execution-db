# BEOED v0.1–v0.4 build notes

## v0.1 predictive execution layer
A product-destination **entry** observation is eligible when Bangladesh exports are below the configured threshold at year `t`; the outcome is whether exports cross the threshold in any of `t+1...t+3`. Features use information available at `t` only.

A **survival** cohort is a newly entered relationship: below threshold at `t-1`, at/above threshold at `t`. The outcome is whether the relationship remains at/above threshold at `t+3`. The survival model is conditional on observed entry.

Validation is temporal: the latest eligible cohort year is held out (or the latest two where needed for outcome variation), then the final model is refit on all historically observable cohorts. Report AUC, Brier score, event rates and cohort years. Do not market an unvalidated probability as a forecast.

## v0.2 product-space layer
The latest BACI country-product export matrix is converted to Balassa RCA. The binary `RCA >= 1` matrix is normalized by country diversity and product ubiquity. A singular-value decomposition supplies the non-trivial country/product eigenvectors used for ECI/PCI. Sign is oriented to make ECI positively related to diversity where identifiable, then scores are standardized.

Bangladesh product density uses standard co-export proximity:
`phi_pq = cooccurrence(p,q) / max(ubiquity_p, ubiquity_q)`.
Density is the proximity-weighted share of related products in which Bangladesh has RCA >= 1. Self-proximity is removed.

These are replications of established complexity concepts, not proprietary intellectual property. BEOED's intended proprietary contribution is the execution and constraint layer built on top.

## v0.3 firm registry
Public EPB company/factory records are normalized into:
- `firm_registry`: one row per exporter record;
- `firm_product_links`: one row per observed firm x HS code.

The current seed is deliberately incomplete. Expansion should be systematic and versioned. Never silently infer missing HS codes. Company contact people, phones and personal email addresses are excluded from the public release.

Candidate matching begins conservatively at shared HS4 and is labelled `observed_related_hs4`, not `can_produce`. Better matching can later use machinery, certifications, product descriptions, association membership, audited disclosures and client-provided data.

## v0.4 domestic value capture
Gross export opportunity is not the same as domestic economic value. BEOED v0.4 is designed to attach documented sector priors for domestic value added, imported-input content, labour intensity, energy intensity and financing intensity. Initial mappings are sector priors; firm-level values require firm data.
