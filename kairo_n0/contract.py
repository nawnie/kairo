"""Teacher/learner boundary for the small Kairo-N0 helper.

Only independently verified observations may cross into N0 training.  The
contract intentionally rejects evaluator truth and canonical acceptance data.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


FORBIDDEN_FIELDS = frozenset({
    "expected_artifact", "evaluator_model", "hidden_state", "exactness",
    "goal_achieved", "posthoc_correctness", "private_case",
})


@dataclass(frozen=True)
class VerifiedObservation:
    task_family: str
    episode_id: str
    prefix: tuple[str, ...]
    output: str
    verification_id: str

    def learner_record(self):
        return {"prefix": list(self.prefix), "output": self.output}


def freeze_split(observations, heldout_families):
    heldout = frozenset(heldout_families)
    train = [row for row in observations if row.task_family not in heldout]
    test = [row for row in observations if row.task_family in heldout]
    train_ids = {row.episode_id for row in train}; test_ids = {row.episode_id for row in test}
    if train_ids & test_ids:
        raise ValueError("episode overlap between train and held-out split")
    if not train or not test:
        raise ValueError("both train and held-out observations are required")
    return tuple(train), tuple(test)


def teacher_export(observations):
    records = []
    for row in observations:
        if not isinstance(row, VerifiedObservation) or not row.verification_id:
            raise ValueError("only verified observations may be exported")
        records.append(row.learner_record())
    return tuple(records)


def reject_privileged_payload(payload):
    keys = set(payload) if isinstance(payload, dict) else set()
    forbidden = keys & FORBIDDEN_FIELDS
    if forbidden:
        raise ValueError("privileged evaluator fields cannot enter N0: " + ",".join(sorted(forbidden)))


def receipt(config, train, heldout, initial_loss, final_loss, peak_bytes=None):
    body = {
        "config": config,
        "train_count": len(train),
        "heldout_count": len(heldout),
        "train_episode_hash": hashlib.sha256(json.dumps(sorted(row.episode_id for row in train)).encode()).hexdigest(),
        "heldout_episode_hash": hashlib.sha256(json.dumps(sorted(row.episode_id for row in heldout)).encode()).hexdigest(),
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "peak_working_set_bytes": peak_bytes,
        "proposal_only": True,
        "evaluator_fields_in_learner": False,
    }
    body["receipt_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return body
