# Kairo Gauntlet Run 1

Date: 2026-09-10

This is the first executable run of the gauntlet against the currently
implemented lanes. It is a boundary-finding report, not a claim that every
protocol gate has been implemented.

## Scorecard

| Lane | Status | Evidence |
|---|---|---|
| Current R24/path tests | PASS | 32 tests passed |
| Current R23 regression tests | PASS | 12 tests passed |
| R40 new schemas/values/bindings | PASS task/artifact gate | 12/12 artifacts verified; 0/12 exact models |
| Historical R23 clean reproduction | INTEGRITY BLOCK | Receipt source hashes mismatch in `kairo_r11/learn.py`, `kairo_r23/challenges.py`, `kairo_r23/client.py`, and `tests_r23/test_challenges.py` before the audit could run |
| Noise and transient-failure gate | NOT IMPLEMENTED | No noise adapter exists yet |
| Hidden late-state gate | NOT IMPLEMENTED | No dedicated late-state adapter exists yet |
| Cross-domain transfer gate | NOT IMPLEMENTED | No isolated cross-domain runner exists yet |

## R40 result

R40 changed table and column schemas, row counts, values, and operation
bindings while keeping the SQLite transaction family. Cold, retained,
random-challenge, and plan-challenge policies each completed 3/3 tasks and
passed 3/3 independent artifact checks. Each policy produced 0/3 exact finite
models. Query totals were 1,116 cold, 1,172 retained, 1,215 random, and 1,215
planned. Retention therefore did not beat cold on this held-out presentation.

## Interpretation

Kairo currently handles unfamiliar data and operation permutations well enough
to produce correct checked artifacts, but its learned model does not transfer
exactly. The historical receipt mismatch is a reproducibility/integrity issue,
not evidence of a capability failure; it must be resolved or explicitly
re-baselined before using the old clean-reproduction result as a fresh pass.

The next executable gate should be a hidden late-state adapter, followed by a
noise/failure adapter and then a genuinely cross-domain transfer run.
