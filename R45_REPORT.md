# Kairo R45: shallow-model challenge stress test

Date: 2026-09-10

R45 held the R43 file-backed deployment workflow constant but forced
`learning.middle_depth: 1`, a deliberately shallow acquisition setting. The
adapter has 11 independently enumerated projected states. This tests whether
challenge selection can find an underfit model's hidden distinction.

## Result

| Policy | Tasks | Successful artifacts | Exact independent models | Challenge mismatches | Queries |
|---|---:|---:|---:|---:|---:|
| plan_challenges | 3 | 3/3 | 0/3 | 0 | 1,806 |
| random_challenges | 3 | 3/3 | 0/3 | 0 | 1,806 |
| backprop_challenges | 3 | 3/3 | 0/3 | 0 | 1,806 |

All nine tasks produced the requested JSON artifact and replayed successfully,
but every learned model remained non-equivalent to the independent 11-state
product. The shallow models therefore passed the task goal while failing the
stronger model criterion. None of the 13 challenge queries per task found the
hidden counterexample, including the backprop-ranked policy.

The first audit implementation was too weak: it checked one access word per
target state and incorrectly reported exactness. The corrected audit now uses
an independent target/learned product traversal and reports 0/9 exact models,
matching the benchmark's false-equivalence results. The correction is
preserved in the receipt and is itself part of the evidence.

## Interpretation

This is a negative result for the current backprop head. It did not improve
challenge discovery over planned or random candidates on a genuinely underfit
model. It also identifies the next engineering target: the challenge
generator, not a larger neural network. Useful exploration must reach outside
the adjacent-swap/deletion candidate family or learn a representation of
unvisited action contexts.

Detailed receipt: `verification/R45_AUDIT.json`.
