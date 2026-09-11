from __future__ import annotations

import json
import random
from pathlib import Path

from kairo_r0.temporal import TemporalReadout


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "r56_retry"
POLICIES = ("targetpool_random", "targetpool_backprop", "targetpool_structured")


def candidate_family(alphabet, cap=8, budget=12):
    a = list(alphabet)
    words = [[a[0], a[1], a[2], a[4], a[7], a[0], a[3]], [a[0], a[1], a[2], a[3], a[4], a[5]], [a[0], a[1], a[4], a[2], a[3], a[5]], [a[0], a[1], a[5], a[2], a[4]], [a[0], a[1], a[6], a[4]], [a[0], a[1], a[7], a[4]], [a[0], a[4], a[1], a[2], a[3]], [a[0], a[1], a[2], a[4], a[3]]]
    return [word for word in words if len(word) <= budget][:cap]


def prechallenge_action_trace(events):
    values = []
    for event in events:
        request = event.get("request", {})
        if request.get("op") == "task_checkpoint": break
        if request.get("op") == "query": values.extend(request["word"])
    return values


def r0_order(observed, alphabet, candidates):
    if not observed: return candidates
    positions = {action: index / max(1, len(alphabet) - 1) for index, action in enumerate(alphabet)}
    sequence = [positions[action] for action in observed]
    model = TemporalReadout(8, nonlinear=True).fit(sequence, sequence)
    scores = []
    for index, word in enumerate(candidates):
        numeric = [positions[action] for action in word]
        errors = [abs(model.predict(numeric[:offset]) - numeric[offset]) for offset in range(1, len(numeric))]
        scores.append((sum(errors) / len(errors) if errors else 0.0, word, index))
    return [word for _, word, _ in sorted(scores, key=lambda row: (-row[0], row[1]))]


def first_mismatch(policy, case_id):
    result = json.loads((RESULTS / policy / case_id / "RESULT.json").read_text())
    mismatches = {tuple(row) for row in result.get("mismatching_words", [])}
    events = json.loads((RESULTS / policy / case_id / "EVENTS.json").read_text())
    order = [tuple(event["request"]["word"]) for event in events if event.get("request", {}).get("purpose") == "challenge"]
    return next((index + 1 for index, word in enumerate(order) if word in mismatches), None), len(order)


def run():
    rows = []
    for policy in POLICIES:
        for case_dir in sorted((RESULTS / policy).glob("D*")):
            boot = json.loads((case_dir / "BOOTSTRAP.json").read_text()); events = json.loads((case_dir / "EVENTS.json").read_text())
            pool = candidate_family(boot["alphabet"]); order = r0_order(prechallenge_action_trace(events), boot["alphabet"], pool)
            result = json.loads((case_dir / "RESULT.json").read_text()); mismatches = {tuple(row) for row in result.get("mismatching_words", [])}
            r0_rank = next((index + 1 for index, word in enumerate(order) if tuple(word) in mismatches), None)
            actual_rank, actual_count = first_mismatch(policy, case_dir.name)
            rows.append({"policy": policy, "case": case_dir.name, "r0_rank_from_prechallenge_only": r0_rank, "actual_rank": actual_rank, "actual_challenges": actual_count, "mismatch_count": len(mismatches), "candidate_count": len(pool)})
    return {"experiment": "R62-R0-offline-context", "rows": rows, "goal_achieved": False}


if __name__ == "__main__":
    result = run(); path = ROOT / "verification" / "R62_R0_OFFLINE.json"; path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print(json.dumps(result, indent=2, sort_keys=True))
