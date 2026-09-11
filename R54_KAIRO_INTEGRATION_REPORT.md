# R54: canonicalized N1 on real Kairo file workflows

Date: 2026-09-11

The canonicalized N1 head was wired into a separate child-process benchmark
using the existing three file-backed Kairo cases (D1-D3). The raw neural,
canonicalized neural, and matched random lanes used the same symbolic learner,
budgets, fresh observations, and independent acceptance gates.

| Policy | Success | Exact models | Replay | Queries |
|---|---:|---:|---:|---:|
| Random challenge control | 3/3 | 3/3 | 3/3 | 7,934 |
| Raw action neural | 3/3 | 3/3 | 3/3 | 7,934 |
| Canonicalized N1 | 3/3 | 3/3 | 3/3 | 7,934 |

The independent R54 audit found 9/9 verified artifacts, 9/9 exact product
models, and 9/9 replay passes across all lanes. N1 therefore preserved the
Kairo safety/correctness boundary, but earned no integration credit on this
workload: all policies were forced to scan the same fixed 13-challenge budget.
This is an integration-neutral result, not evidence that N1 is useless.

Decision: keep the canonicalized representation, do not fuse or assign a
weight yet, and run the next real Kairo test with an early-stop/query-budget
protocol where proposal ordering can affect cost. The independent N1 transfer
pass and the R53 raw-head 0/4 negative remain preserved.

Receipt: `verification/R54_AUDIT.json`.
