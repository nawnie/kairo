# Kairo R48: adaptive conformance-depth escalation

Date: 2026-09-10

R48 retested the R45 shallow-model failure with `middle_depth: 1` and
`max_middle_depth: 2`. The learner was allowed to increase conformance depth
only after its bounded depth-1 sweep found no counterexample. No evaluator
state, exactness result, or private witness was supplied to the learner.

## Result

| Policy | Tasks | Artifacts | Exact independent models | Replays | Queries |
|---|---:|---:|---:|---:|---:|
| plan_challenges | 3 | 3/3 | 3/3 | 3/3 | 8,072 |
| random_challenges | 3 | 3/3 | 3/3 | 3/3 | 8,072 |
| backprop_challenges | 3 | 3/3 | 3/3 | 3/3 | 8,072 |

Every task recorded the internal event `conformance_depth_growth` from 1 to
2. The independent audit found the 11-state products, matched all models,
reopened all artifacts, and replayed all traces.

## Interpretation

R48 fixes the R45 underfit boundary through a bounded, evidence-driven
representation escalation. It does not claim unrestricted competence: the
maximum depth is explicitly capped, and the cost is substantial compared with
R45's 602 queries per task (about 2,700 here). The result supports adaptive
conformance as a more useful next direction than enlarging the neural head.

The neural challenge selector remains neutral; exactness came from the
learner's own conformance-depth growth. Future work should learn when and how
to allocate escalation cost across genuinely new domains, under the safety
gate.

Receipt: `verification/R48_AUDIT.json`.
