"""Deterministic CRM evidence boundary; semantic providers remain advisory.

Context and canonical records MUST be supplied by the authenticated CRM server,
not by the model or browser. This module grants no execution authority.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def timestamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timezone required')
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class Context:
    tenant_id: str
    property_ids: tuple[str, ...]
    actor_id: str
    run_id: str

    def __post_init__(self):
        if not all((self.tenant_id, self.actor_id, self.run_id)) or not self.property_ids:
            raise ValueError('authenticated scope and run ID required')


@dataclass(frozen=True)
class Evidence:
    source_id: str
    tenant_id: str
    property_id: str
    record_id: str
    field: str
    value: Any
    revision: int
    observed_at: str
    expires_at: str
    source_hash: str
    canonical: bool = False

    def __post_init__(self):
        if not all((self.source_id, self.tenant_id, self.property_id, self.record_id,
                    self.field, self.source_hash)):
            raise ValueError('complete provenance required')
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError('nonnegative integer revision required')
        if timestamp(self.expires_at) <= timestamp(self.observed_at):
            raise ValueError('invalid evidence validity interval')
        digest(self.value)


@dataclass(frozen=True)
class Review:
    status: str
    value: Any
    evidence_ids: tuple[str, ...]
    reasons: tuple[str, ...]


def review(context, evidence, record_id, field, now):
    """Exact field lookup. No semantic equivalence or freshness inferred from prose."""
    clock = timestamp(now)
    selected = []
    excluded = False
    for item in evidence:
        if item.tenant_id != context.tenant_id or item.property_id not in context.property_ids:
            continue
        if item.record_id != record_id or item.field != field:
            continue
        if timestamp(item.observed_at) > clock or timestamp(item.expires_at) <= clock:
            excluded = True
            continue
        selected.append(item)
    if not selected:
        return Review('abstain', None, (), ('stale_or_missing_evidence' if excluded else 'missing_evidence',))
    ids = tuple(sorted({e.source_id for e in selected}))
    if len({digest(e.value) for e in selected}) != 1:
        return Review('conflict', None, ids, ('contradictory_sources',))
    canonical = [e for e in selected if e.canonical]
    if not canonical:
        return Review('unverified', None, ids, ('no_canonical_crm_record',))
    return Review('supported', json.loads(json.dumps(canonical[0].value)), ids,
                  ('canonical_snapshot_only',))


@dataclass(frozen=True)
class Change:
    record_id: str
    property_id: str
    field: str
    before: Any
    after: Any
    expected_revision: int
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    payload_json: str

    def payload(self):
        return json.loads(self.payload_json)


def propose(context, changes, evidence, allowed_fields, now, expires_at):
    """Build an immutable preview after canonical revision and source checks.

    allowed_fields is trusted server configuration. Only nonfinancial task,
    relationship and evidence metadata should be enabled in the initial lane.
    """
    if not changes or timestamp(expires_at) <= timestamp(now):
        raise ValueError('changes and future expiration required')
    normalized = []
    targets = set()
    for change in changes:
        target = (change.property_id, change.record_id, change.field)
        if target in targets:
            raise ValueError('duplicate target')
        targets.add(target)
        if change.property_id not in context.property_ids or change.field not in allowed_fields:
            raise ValueError('change outside authorized scope')
        candidates = [e for e in evidence if e.tenant_id == context.tenant_id
                      and e.property_id == change.property_id and e.record_id == change.record_id
                      and e.field == change.field]
        check = review(context, candidates, change.record_id, change.field, now)
        canonical = [e for e in candidates if e.canonical
                     and timestamp(e.observed_at) <= timestamp(now) < timestamp(e.expires_at)]
        if check.status != 'supported' or digest(check.value) != digest(change.before):
            raise ValueError('current canonical value required')
        if any(e.revision != change.expected_revision for e in canonical):
            raise ValueError('stale record revision')
        if not change.evidence_ids or not set(change.evidence_ids).issubset(check.evidence_ids):
            raise ValueError('valid source references required')
        normalized.append(asdict(change))
    payload = dict(schema_version=1, context=asdict(context), changes=normalized,
                   created_at=now, expires_at=expires_at,
                   status='pending_human_approval', execution_authority=False)
    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                            ensure_ascii=False, allow_nan=False)
    return Proposal(digest(payload), serialized)


def validate_approval(proposal, context, approved_hash, selected_indices,
                      current_revisions, now, can_approve):
    """Validate selection for a CRM command adapter, without executing it.

    can_approve and revisions come from server authorization/current DB reads.
    The command adapter must repeat these checks inside its write transaction,
    enforce single-use/idempotency, and persist approval/outbox/audit atomically.
    """
    payload = proposal.payload()
    if not can_approve or digest(payload) != proposal.proposal_id or approved_hash != proposal.proposal_id:
        raise ValueError('approval or exact proposal hash invalid')
    if payload['context'] != json.loads(json.dumps(asdict(context))):
        raise ValueError('approval context mismatch')
    if not timestamp(payload['created_at']) <= timestamp(now) < timestamp(payload['expires_at']):
        raise ValueError('approval outside validity interval')
    if not selected_indices or len(set(selected_indices)) != len(selected_indices):
        raise ValueError('unique selected changes required')
    selected = []
    for index in selected_indices:
        if type(index) is not int or not 0 <= index < len(payload['changes']):
            raise ValueError('invalid selection')
        change = payload['changes'][index]
        key = (change['property_id'], change['record_id'])
        if current_revisions.get(key) != change['expected_revision']:
            raise ValueError('record changed since preview')
        selected.append(change)
    return selected
