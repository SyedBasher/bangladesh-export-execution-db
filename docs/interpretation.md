# Interpretation and cautions

1. **Large market is not high potential.** A large destination-product market may be inaccessible because of tariffs, standards, buyer structure, technology or firm capability.
2. **Low Bangladesh share is not automatically an opportunity.** It can reflect comparative disadvantage or a binding constraint.
3. **Unit values are not prices in every HS6 line.** Quantity units can be heterogeneous; use quantity-derived measures only after checking unit meaning and coverage.
4. **BACI is for internationally comparable merchandise trade.** Do not splice Bangladesh fiscal-year EPB/BB series directly into BACI calendar-year panels without explicit reconciliation.
5. **Prediction is not causation.** Entry/persistence probabilities describe patterns in historical transitions. They do not estimate the causal effect of removing a particular constraint.
6. **Firm matching is probabilistic unless directly observed.** Public registries do not provide complete firm × HS6 × destination customs histories.

## Reading capability evidence

`capability_evidence_status` separates persistent export evidence from recent signals. A recent USD 1 million export is not automatically interpreted as an emerging productive capability. `recent_export_signal_requires_validation` exists precisely for cases that may reflect a one-off shipment, re-export, temporary arbitrage, or genuinely new production that has not yet persisted.

`feasibility_archetype` is a triage device. In particular, product-space proximity to a basic metal, primary chemical, fertilizer, scrap stream, or advanced-technology product should not be read the same way as proximity to a fabricated downstream product. The database therefore produces separate validation samples for downstream manufacturing, process industry, advanced technology, and recent export signals.
