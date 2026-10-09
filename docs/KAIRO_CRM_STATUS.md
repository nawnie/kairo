# Kairo CRM branch status — 2026-10-09, v0.2

Branch: feature/kairo-crm. Original public baseline:
ba48380cd70e355f07b35badbee6350e182f8dc5.

Implemented: scoped structured evidence review, immutable proposal previews,
selected approval validation, local JSON-lines review transport and synthetic
SQLite command adapter. The adapter stores canonical tasks and proposals,
rechecks synthetic permissions and revisions inside a write transaction, applies
only selected changes and commits receipt/outbox with the record update.
Exact retries return the original result; changed selections are rejected.

Validation: 27/27 synthetic tests pass, including exception-injected rollback,
reopening the database before retry, two sequential connections, revoked grants,
cross-tenant/actor denial, stale versions, expiry, before-value mismatch and
invalid semantic candidates. Reproduce:
python -m unittest tests_crm tests_crm_sandbox -v

Limits: synthetic structured fixtures only; no semantic model, learner/service
integration, production authentication, actual CRM adapter, sync worker,
OS process-kill/power-loss test, concurrent load or hardware benchmark.
The unchanged tests_r24 baseline has four errors caused by missing kairo_r11.
No live CRM data or production database was used. The sandbox is a reference
implementation, not production-ready CRM software.

Next: connect real task/owner-project adapters and an advisory semantic provider;
score held-out operational questions separately from transaction correctness.
