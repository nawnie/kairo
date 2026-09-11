# R51-R0: isolated dynamic-context proof

R0 is a CPU-only nonlinear-variation readout candidate, kept separate from
the symbolic Kairo learner. It receives sequence observations and may emit
temporal predictions only; it is not evidence and cannot authorize a Kairo
claim.

The frozen comparison is 3 regimes (`delayed`, `parity`, `reversal`) × 5
seeds. Each case trains on one generated sequence and evaluates on a disjoint
sequence with the regime rule hidden from the learner. Controls are a
constant-history base (`width=1`), a nonlinear fixed-window readout
(`width=3`), and R0 (`width=8`). The readout is ridge-regularized and the
serialized model must reproduce predictions exactly.

R0 can continue only if it beats the fixed-window control on a predeclared
majority of cases, matches or beats the base on the ordinary cases, and
survives save/reload. A lower training loss alone is not evidence of useful
dynamic context.
