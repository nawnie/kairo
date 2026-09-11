# R55: early-stop challenge-cost control

Date: 2026-09-11

R55 used deliberately shallow acquisition (`middle_depth=1`) and identical
13-candidate challenge pools for random, raw-neural, and canonicalized-N1
lanes. The termination rule was lane-independent: stop only after a fresh
challenge mismatch; otherwise consume the full pool.

| Lane | Artifacts | Exact models | Replays | Queries | Mismatches |
|---|---:|---:|---:|---:|---:|
| Random | 3/3 | 0/3 | 3/3 | 1,806 | 0 |
| Raw neural | 3/3 | 0/3 | 3/3 | 1,806 | 0 |
| Canonical N1 | 3/3 | 0/3 | 3/3 | 1,806 | 0 |

No policy reached a counterexample, so early stopping never triggered and no
query-cost separation was possible. The shallow models remained
non-equivalent despite producing the requested artifacts, matching the
earlier R45-R47 failure pattern. This is a neutral result, not evidence
against N1.

An initial R55 attempt used the broader coverage generator only for the
structured lane and is explicitly invalid; it is not included in the receipt.
The next experiment must provide a changed-binding workload with a reachable
counterexample while retaining identical candidate pools and independent
artifact/exact/replay audits.

Receipt: `verification/R55_AUDIT.json`.
