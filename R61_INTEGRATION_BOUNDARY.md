# R61 typed integration boundary

R61 records the first integration prerequisite after the isolated R0 weight
sweep. `DynamicContext` carries only bounded R0/R1 features, model
provenance, observed event IDs, and an explicit weight. `NeuralProposal` is
separate and remains N1-only. `CanonicalResult` is immutable and locked before
natural-language rendering or online updates.

The contract test proves that applying R0 context or an N1 proposal cannot
change canonical authority. This is an interface safety gate, not a claim
that R0 has yet improved a real Kairo workload. That workload remains the next
required experiment before choosing a production weight.
