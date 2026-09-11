# R62: offline real-Kairo R0 context replay

Date: 2026-09-11

R62 replayed the frozen R56 real-Kairo candidate families. The R0 context
scorer was fit only from query action prefixes before each task checkpoint.
Mismatch records and independent results were read only after scoring for
audit; they were not learner inputs.

For D1, the reachable mismatch ranks were:

| Lane | First mismatch |
|---|---:|
| Random | 2 |
| Raw neural | 6 |
| Canonical N1 | 4 |
| R0 context replay | 4 |

D2 and D3 had no reachable mismatch in the frozen eight-candidate family, so
they are censored rather than counted as successes. R0 context improved over
the raw neural lane but did not beat random or N1. This is neutral integration
evidence, and it is offline replay rather than a live production integration.

Decision: keep R0 eligible for a better real workload, but assign no Kairo
weight yet. The next live test needs at least two of three changed-binding
cases with reachable distinctions and complete typed context/resource
receipts.

Receipt: `verification/R62_R0_OFFLINE.json`.
