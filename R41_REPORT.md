# Kairo R41: the R40 exactness failure was undercoverage, not an expressiveness wall

Date: 2026-09-10

R41 was a controlled audit of the claim that R40's zero exact models showed a
grammar or expressiveness ceiling. It reproduced R40, changed one learner
setting, and then tested six fresh SQLite cases. The learner, backend, child
process boundary, action alphabet, goals, challenge code, and evaluator were
otherwise unchanged.

## Result

| Lane | Policies | Tasks | Correct artifacts | Exact projected models | Queries |
|---|---:|---:|---:|---:|---:|
| R40 reproduced, depth 1 | 4 | 12 | 12/12 | 0/12 | 4,718 |
| R40 reproduced, depth 2 | 4 | 12 | 12/12 | 12/12 | 16,287 |
| Fresh schemas/values/bindings, depth 2 | 2 | 12 | 12/12 | 12/12 | 11,953 |

The R40 reproduction was exact at depth 1: every original policy reproduced
its original summary and task outputs. The only change in the successful lane
was `learning.middle_depth: 1 -> 2`, the same conformance depth already used
by the successful R27 and R35 SQLite runs.

At depth 1, each R40 target had seven reachable projected states and the
learner retained six. At depth 2, the first conformance pass found the exact
seven-action witness that R40's evaluator had found, acquired a new
distinguishing suffix, and completed a seven-state model. The independent R41
BFS comparator found no counterexample for all twelve depth-2 R40 tasks.

The first cold R40 E task shows the mechanism directly. The depth-1 witness
was:

```text
open -> begin -> stage -> commit -> close -> open -> inspect
```

The learned model predicted `baseline_verified`; the SQLite system returned
`durable_verified`. Depth 2 observed this witness during conformance, added the
distinguishing suffix `open -> inspect`, and completed the model. This is a
missing observation distinction, not an unrepresentable state.

## Fresh held-out cases

The six fresh cases used row counts 1, 17, 64, 3, 32, and 127; new table and
column names; new values; and three seeded action-binding permutations. Cold
and retained policies each produced six successful tasks, six independently
verified databases, and six exact projected models.

Retention used 4,053 queries versus 7,900 cold queries, saving 3,847 queries
(48.7%) on this held-out lane. It reused the exact model with one validation
query on the three unchanged-binding cases and reacquired after each changed
binding. The retained policy therefore did not fail universally; its R40
regression was caused by the shallow learned model and binding changes.

## What this does and does not refute

R41 refutes the narrow inference that R40's `0/12` exact models demonstrate a
grammar or expressiveness ceiling for this SQLite transaction interface. The
same learner and same interface reach exact seven-state models when conformance
coverage is increased, and the result transfers across six fresh finite cases.

Claude's cost criticism remains valid. Depth 2 costs about 3.56 times the R40
cold queries, and R40's plan and random challenge policies still found no
extra error. R41 does not show a planning advantage. It shows that the
acquisition depth, which R40 set to 1 despite R27/R35 evidence, was the causal
reason R40 underfit this seven-state interface.

The R40 plan and random challenge words were not byte-identical. Their result
hashes differ and their concrete words differ; their proposal lengths and
aggregate costs were matched. Equal outcomes are a real negative result for
that challenge policy on this workload.

R41 establishes a stronger bounded claim: Kairo can learn and retain exact
models of this finite SQLite transaction family under sufficient conformance
coverage, with independently replayed observations and artifacts. It does not
establish unrestricted SQLite competence, arbitrary software understanding,
autonomous primitive invention, or true intelligence. Those remain the next
tests rather than being smuggled into this result.

## Integrity evidence

`verification/R41_AUDIT.json` independently checked 36 tasks, replayed 33,372
event records, independently reopened every delivered database, checked schema,
rows, and `PRAGMA integrity_check`, compared primary and fresh reproduction
trees, and performed a separate product traversal. The audit preserved 5,789
prior files and verified their hashes. The R41 dataset and source freeze are
recorded under `datasets/r41/`.

The local audit is the authoritative detailed receipt; this report is the
public interpretation of that receipt. Its verdict is limited to the frozen
finite adapters and the stated fresh holdouts.
