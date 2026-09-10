# Kairo R42: savepoint-family transfer

Date: 2026-09-10

R42 tested the same learner against a changed SQLite behavior family rather
than another renamed R40 table. Each case exposed eight opaque actions,
including `savepoint` and `rollback_to_savepoint`, and required a pending
inspection, savepoint recovery, durable commit, and session close.

## Result

| Policy | Tasks | Successful artifacts | Exact independent models | Queries |
|---|---:|---:|---:|---:|
| cold | 3 | 3/3 | 3/3 | 10,519 |
| retain | 3 | 3/3 | 3/3 | 10,759 |
| random_challenges | 3 | 3/3 | 3/3 | 10,807 |
| plan_challenges | 3 | 3/3 | 3/3 | 10,807 |

All twelve tasks reached the required goal. The independent product audit
found 18 projected states per case, compared every learned transition and
output against that product, reopened every delivered SQLite artifact in a
fresh read-only connection, checked `PRAGMA integrity_check`, and replayed
the recorded step events against fresh databases. All twelve artifact checks,
model checks, and replays passed.

## Interpretation

This is stronger evidence against the narrow R40 conclusion that Kairo's
zero exact models demonstrated a grammar or expressiveness ceiling. R42's
model is exact on a larger 18-state projected interface with savepoint
semantics, fresh schemas, fresh values, and three binding permutations.

It does not prove unrestricted software understanding or general
intelligence. The adapter remains finite and deliberately specified. The
next serious boundary is a cross-domain adapter whose state and artifact
semantics are not SQLite transactions; R42 is evidence that the R40 failure
was not a generic failure to represent deeper finite state.

The planning result remains neutral: plan and random challenge policies had
identical aggregate query totals and identical exact outcomes on this small
workload. That is still an open optimization question, not evidence against
the core learner.

Detailed machine-readable receipt: `verification/R42_AUDIT.json`.
