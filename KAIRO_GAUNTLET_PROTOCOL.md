# Kairo Gauntlet: pushing current domains to failure

Purpose: find the first honest boundary where Kairo stops answering correctly,
while separating task success, model correctness, transfer, and safe abstention.

The gauntlet uses fresh holdouts. Learners receive only declared action
alphabets and their own observations. Expected answers, target models, hidden
state counts, binding meanings, and artifact checkers remain evaluator-side.
Every run records correct, false-supported, abstained, evidence, cost, and
artifact outcomes separately.

## Gates

### 0. Baseline accounting

Re-run the CSV, SQLite, and path-question lanes, plus R40. Verify source
hashes, fresh-process replay, artifact hashes, and full query/action budgets.

### 1. Interpolation stress

Use unseen values, row counts, empty and singleton inputs, maximum-size inputs,
longer valid action words, and every unused action-binding permutation.

### 2. Composition stress

Use multiple valid workflows, equivalent orderings, commit/rollback/reopen
interleavings, changed CSV schemas and numeric formats, and SQLite savepoint or
repeated-begin edge cases. This tests reusable relations instead of one plan.

### 3. Hidden-state and late-change stress

Add evaluator-only states reachable only after long prefixes, threshold changes,
same-prefix/different-future histories, and previously unused action pairs.
Measure first discovery, false support before discovery, repair cost, and fresh
process persistence.

### 4. Imperfect-observation stress

Test bounded output noise, transient failed probes, recoverable resets, and
independent artifact failures. Abstention must beat a confident wrong answer.

### 5. Source-question stress

Use unseen mixed-language projects and ask indirect purpose, dependency,
entrypoint, side-effect, and call-path questions; include absent answers,
ambiguous names, misleading documentation, generated files, and unsupported
claims. Keyword overlap alone is not correctness.

### 6. Cross-domain transfer

Retain on one domain, then test a different domain with no shared operation
meanings: CSV to SQLite, SQLite to filesystem, or source inspection to a
stateful adapter. Do not transfer domain-specific goal checkers or grammars.

## Failure rules

Freeze the first case when a held-out answer is wrong, an artifact is wrong,
retention costs more than cold after full accounting, repair accepts an
unverified model, or Kairo overconfidently answers outside its evidence. Repro-
duce it in a fresh process, classify it, then continue the other gates.

## Required scorecard

`task_correct`, `artifact_correct`, `exact_model`, `supported_correct`,
`false_supported`, `abstained`, `evidence_relevant`, `query_cost`,
`input_symbol_cost`, `action_cost`, `repair_cost`, `fresh_reproduction`, and
`failure_case_ids`.

No aggregate may hide false support or turn finite-adapter exactness into a
claim of general intelligence.
