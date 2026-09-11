# R51-N0 result: observed-trace proposal transfer

Date: 2026-09-11

The bounded probe trained the existing small backpropagation head on donor
prefix/output observations, then ranked 80 fresh candidate words. The hidden
target was held outside the learner. Across five deterministic initialization
seeds, N0 reached the target before the mean of 25 matched random orderings in
4/5 runs. Neural ranks were 17, 23, 26, 2, and 67; the one rank-67 result is
an explicit instability, not a success to hide.

Therefore N0 is **not promoted**. The probe demonstrates that the head can
train and sometimes improve proposal ordering, but it does not yet establish
reliable transfer. The next N experiment must use an invariant/structured
representation for changed bindings, keep the same held-out protocol, and
require a majority win with no harmful exactness or replay regression.

This remains an auxiliary proposal experiment. It cannot certify a model,
replace symbolic conformance, or use hidden evaluator labels.
