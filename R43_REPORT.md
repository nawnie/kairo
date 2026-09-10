# Kairo R43: transfer to a file-backed deployment workflow

Date: 2026-09-10

R43 moved the experiment outside SQLite. The adapter persisted a JSON
deployment artifact and exposed opaque actions for opening a session, editing
a draft, validating it, publishing it, reloading the published artifact,
rolling back an in-memory draft, inspecting local versus persisted state, and
closing the session.

## Result

| Policy | Tasks | Successful artifacts | Exact independent models | Queries |
|---|---:|---:|---:|---:|
| cold | 3 | 3/3 | 3/3 | 7,895 |
| retain | 3 | 3/3 | 3/3 | 7,895 |
| random_challenges | 3 | 3/3 | 3/3 | 7,934 |
| plan_challenges | 3 | 3/3 | 3/3 | 7,934 |

The three cases used different services, versions, route lists, baseline
documents, draft documents, and action-binding permutations. The independent
audit found 11 projected states per case, compared every learned transition
and output against that product, reopened all twelve JSON artifacts, and
replayed all twelve recorded step traces against fresh file backends. Every
artifact, exactness, and replay check passed.

## Interpretation

R43 is evidence that the R40 failure was not a generic inability to represent
state outside the original shallow SQLite presentation. The same observation
learner reached exact finite models for a different persistence format and a
different workflow structure.

The result remains bounded. This is a deliberately specified file-backed
adapter, not arbitrary program comprehension, open-world source reasoning, or
proof of general intelligence. It also does not establish a planning benefit:
random and planned challenges had the same aggregate cost and outcome here.

The next boundary should be a supplied, previously unseen real program
directory where Kairo must answer source/runtime questions and where the
oracle checks both the answer and artifact effects without exposing private
evaluator labels to the learner.

Detailed receipt: `verification/R43_AUDIT.json`.
