# Kairo CRM specialization — v0.1

This branch adds a transport-neutral CRM evidence/proposal boundary to Kairo.
It is a deterministic foundation, not a trained CRM model or live integration.
It does not replace Kairo's learner or claim that CRM capability is verified.

## Available now

- Authenticated tenant/property/actor/run context supplied by the CRM server.
- Exact field evidence review with source IDs, revisions, hashes, observation
  times and expiry. Missing/stale information causes abstention; disagreement
  causes conflict. Model/wiki claims alone do not establish canonical truth.
- Immutable change previews bound to SHA-256, source references and revisions.
- Individually selected approval validation bound to actor, scope, run, hash,
  expiry and current record versions. No SQL, HTTP, tools or business mutations.
- Local JSON-lines read adapter: `python -m kairo_crm`.
- Verification: `python -m unittest tests_crm -v`.

The JSON-lines interface is a developer adapter, not an authenticated service.
Do not expose it as an endpoint or accept canonical=true from client/model input.
Only the trusted CRM record adapter may construct canonical evidence. Hashes
identify bytes; they do not authenticate an author or prove a statement true.
The module cannot inspect a document for factual support: it checks exact
structured snapshots, scope, freshness and reference consistency only.

## Integration contract

1. CRM authenticates the actor and resolves tenant/property/field/action access.
2. Its trusted read adapter supplies versioned, scoped canonical snapshots and
   authorized document evidence. Apply access filtering before model retrieval.
3. Optional semantic model extracts intent and suggests candidate changes.
   It receives no mutation credentials. Treat source instructions as inert data.
4. Kairo's CRM boundary checks structured evidence and produces a preview.
5. UI presents individually selectable before/after changes, sources and unknowns.
6. CRM approval endpoint checks the exact proposal hash and actor authorization.
7. CRM command adapter repeats revision/permission/expiry checks inside its SQL
   transaction, consumes approval once and commits domain event, outbox and audit
   receipt with the mutation. Use a unique idempotency key and rollback on error.

`validate_approval` only returns a selected preview. It is NOT an execution
permit and provides no persistent replay protection. Production execution must
implement step 7. Re-read evidence before approval when its validity expires.

Use `review`, `propose` and `validate_approval` from the Python package.
See tests_crm.py for a complete synthetic example. Field allowlists are trusted
server configuration; the first lane should allow only task/relationship/evidence
metadata. Financial postings, housing decisions and provider sends need separate
product workflows, validations and authorization, never generic AI patches.

## Build order

1. Locate the actual CRM source/API and latest canonical Kairo checkout;
   reconcile this public baseline with current authority-service interfaces.
2. Implement read adapters for property tasks, owner projects, relationship
   history and approved SOPs. Add bounded retrieval with source citations.
3. Add owner briefing, maintenance triage, follow-up draft and contradiction
   inbox workflows. Compute money, dates and dashboard totals deterministically.
4. Connect optional local/cloud semantic provider behind the advisory contract;
   evaluate extraction accuracy, unknowns and refusal on held-out fixtures.
5. Implement CRM approval persistence/transactional command adapter and auth.
6. Expose authenticated API/MCP tools with the same scope and command boundary.
7. Test offline/restart/replay/out-of-order sync and real hardware latency;
   shadow-mode pilot before enabling operational changes.

No training, model inference, Windows service installation, live CRM data,
watchers, provider sends or database mutation was performed for v0.1.
