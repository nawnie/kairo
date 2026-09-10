# Kairo R47: coverage-driven frontier exploration

Date: 2026-09-10

R47 expanded frontier challenges beyond the first short prefixes. It generated
two-, three-, and four-action continuations from the longest access words the
learner had actually observed, then greedily selected candidates with diverse
unobserved action pairs. The backprop head ranked those candidates using only
observed trace/output data.

## Result

| Policy | Tasks | Artifacts | Exact independent models | Detected mismatches | Queries |
|---|---:|---:|---:|---:|---:|
| coverage_backprop | 3 | 3/3 | 0/3 | 0 | 1,815 |
| frontier_challenges | 3 | 3/3 | 0/3 | 0 | 1,815 |
| random_challenges | 3 | 3/3 | 0/3 | 0 | 1,806 |

The independent audit checked nine tasks, found the expected 11-state target
products, independently replayed all traces, and reopened all artifacts.
Every artifact and replay passed; none of the policies found the hidden
underfit-model counterexample.

## Interpretation

Coverage expansion improved candidate length and pair diversity but did not
produce useful discovery under this budget. The limiting issue is now more
specific: observed action-prefix coverage is not enough to infer which
unobserved continuation will distinguish a merged state. The next experiment
must test a genuinely different query strategy or representation, with its
cost charged and the same independent product/replay gate. A larger neural
head is not justified by R44-R47.

Receipt: `verification/R47_AUDIT.json`.
