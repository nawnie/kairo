# Kairo R46: observed-frontier exploration

Date: 2026-09-10

R46 tested whether challenge breadth, rather than adjacent edits alone, would
let Kairo discover the hidden distinction missed by R45's shallow models.
Candidates were generated from access words observed during acquisition. The
backprop policy ranked those candidates using only observed prefix/output
traces.

## Result

| Policy | Tasks | Artifacts | Exact independent models | Detected mismatches | Queries |
|---|---:|---:|---:|---:|---:|
| frontier_challenges | 3 | 3/3 | 0/3 | 0 | 1,815 |
| frontier_backprop | 3 | 3/3 | 0/3 | 0 | 1,815 |
| random_challenges | 3 | 3/3 | 0/3 | 0 | 1,806 |

The independent audit checked nine tasks, replayed all nine traces, and found
the same 11-state target products. Every delivered artifact was correct, but
none of the policies detected the underfit model's counterexample.

## Interpretation

The backprop head still has no demonstrated exploration benefit. The frontier
generator is also not yet broad enough: its fixed first 16 candidates are
dominated by short low-information prefixes. The next experiment should use a
diversity/coverage objective over observed contexts and charge its extra
queries, with a matched control. Enlarging the neural head is not justified by
these results.

Receipt: `verification/R46_AUDIT.json`.
