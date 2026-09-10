# R41: controlled audit of the R40 exactness claim

Freeze this protocol, every executable source, and all inputs before running.
Preserve R5-R40 artifacts. No learner or SQLite backend change is planned.

## Questions and controls

1. Reproduce all four R40 policies on the unchanged E/F/G fixtures at depth 1.
2. Run the same four policies with ONLY learning.middle_depth changed to 2.
   This restores the existing R27 conformance setting. Keep the seeds, query,
   symbol, round, challenge and execution limits unchanged. Do not inject an
   evaluator witness, state count, binding meaning or target into the learner.
3. Run cold and retain at depth 2 on six new authored cases, generated once
   with seed 4102026. Use row counts 1, 17, 64, 3, 32 and 127. Each pair shares
   a new action binding but has new table/column names and rows. Bindings change
   between pairs. Report initial acquisition, same-binding reuse and changed-
   binding transfer separately, including every loss. All require pending,
   close, reopen and durable verification. These are fixed-adapter variants,
   not six independent domains or natural data.
4. Repeat every run in fresh processes and compare every deterministic output
   file, including raw observations and delivered SQLite database bytes.

## Evidence and acceptance

Use unchanged kairo_r24.benchmark, the R23 process/host boundary and the R11-R23
observation learner. The child receives opaque actions, goals, budgets and its
own retained artifact. Evaluation happens after the child exits. Preserve all
queries and input symbols, successful actions, failures and incomplete runs.

Reopen every delivered database with a separate read-only connection; validate
rows, schema and integrity independently of the benchmark artifact checker.
Recompute product equivalence with a separately implemented BFS, and replay
every logged query/action through fresh SQLite backends. Compare all recorded
responses, meters and final artifacts. Tampered model/output/artifact checks
must be rejected by tests. Recheck source/input/prior-result hashes after runs.

Original R40 counterexamples are diagnostic evidence only, evaluated after the
new learner exits; never seed learning with them. Inspect actual challenge
words and lengths instead of inferring byte equality from equal totals.

A depth-2 exact result refutes an expressiveness ceiling for this fixed finite
interface. It does not prove unrestricted SQLite modeling, universal finite
representation, general intelligence, or a planned-challenge advantage. No
guarantee is inferred from provisional agreement. The historical negative
transfer and equal challenge outcomes remain valid unless new evidence says
otherwise. Report increased exploration costs without hiding them.

Full objective remains active. This experiment is a controlled falsification
of a specific diagnosis, not a forecast of inevitable success.
