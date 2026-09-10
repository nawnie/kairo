# Kairo R39: SQLite persistence checkpoint

R39 completed the previously scaffolded SQLite transaction experiment using
the frozen local R24 protocol and synthetic fixtures. The benchmark exercised
staging, commit, rollback, close, reopen, and independent artifact inspection.

| Policy | Task responses | Independently verified artifacts | Exact finite models | Queries |
|---|---:|---:|---:|---:|
| cold | 4/4 | 4/4 | 0/4 | 1,488 |
| retain | 4/4 | 4/4 | 0/4 | 774 |
| random_challenges | 4/4 | 4/4 | 0/4 | 824 |
| plan_challenges | 4/4 | 4/4 | 0/4 | 824 |

The artifact gate independently reopened each produced database and checked
the expected persisted rows plus SQLite integrity. This establishes a real
local transaction-task result and a large retained-model query reduction, but
not an exact learned model: the finite projected-state equivalence check found
counterexamples for every policy. It is also not evidence about SQLite in
general or unrestricted intelligence.

The first run exposed a freeze-schema compatibility defect: `FREEZE.json`
stores the R24 protocol hash without a `protocol_file` field. The benchmark now
validates that hash against `R24_PROTOCOL.md`, while continuing to verify the
frozen fixture hashes.
