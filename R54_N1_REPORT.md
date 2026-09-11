# R54-N1 result: binding-invariant neural transfer

Date: 2026-09-11

N1 was trained on six donor prefix/output observations using a canonical
first-occurrence action-pattern encoding. The held-out family used renamed
bindings and was never passed to training. The small network used 10 input
features, 8 hidden units, 3 output labels, and eight epochs.

| Policy | Held-out accuracy |
|---|---:|
| Raw action-identity head | 60.0% |
| Canonicalized N1 head | 100.0% |
| Deterministic random control mean (25 runs) | 38.4% |

The run took 0.00345 seconds. No evaluator truth entered training, and the
head remained proposal-only. This is a positive isolated N1 representation
gate: canonical structural features rescued transfer that the raw head missed.

It is not yet a Kairo promotion. The next required test is the same
canonicalized helper on fresh Kairo changed-binding program tasks, with
symbolic-only, random, and N-ranked challenge policies plus independent
artifact, exact-model, and replay audits. Fusion weights remain gated.

Receipt: `verification/R54_N1.json`.
