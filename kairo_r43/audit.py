import json
import tempfile
from collections import deque
from pathlib import Path

from kairo_r11.model import Model
from .backend import FileWorkflow, inspect_artifact

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "datasets" / "r43"; RESULTS = ROOT / "results" / "r43_retry"


def product(case, cap=64):
    with tempfile.TemporaryDirectory(prefix="r43-product-") as directory:
        backend = FileWorkflow(Path(directory) / "target", case); backend.reset()
        snapshots = [backend.snapshot()]; words = [[]]; ids = {json.dumps(snapshots[0], sort_keys=True): "s0"}; transitions = {}; index = 0
        try:
            while index < len(words):
                word = words[index]; state = "s" + str(index); transitions[state] = {}
                for action in sorted(case["bindings"]):
                    backend.reset()
                    for prefix in word: backend.step(prefix)
                    output = backend.step(action); snapshot = backend.snapshot(); key = json.dumps(snapshot, sort_keys=True)
                    if key not in ids:
                        if len(words) >= cap: raise AssertionError("product state cap")
                        ids[key] = "s" + str(len(words)); words.append(word + [action]); snapshots.append(snapshot)
                    transitions[state][action] = [ids[key], output]
                index += 1
            return {"initial": "s0", "alphabet": sorted(case["bindings"]), "transitions": transitions}, len(words)
        finally: backend.close()


def replay(case, events):
    with tempfile.TemporaryDirectory(prefix="r43-replay-") as directory:
        backend = FileWorkflow(Path(directory) / "replay", case)
        try:
            for event in events:
                request = event.get("request", {})
                if request.get("op") == "step":
                    if backend.step(request["action"]) != event["response"]["output"]: return False
            return True
        finally: backend.close()


def exact_model(model, target):
    if not model: return False
    learned = Model.from_dict(model)
    if tuple(target["alphabet"]) != learned.alphabet: return False
    positions = {action: index for index, action in enumerate(learned.alphabet)}
    queue = deque([("s0", 0)]); seen = {("s0", 0)}
    while queue:
        target_state, learned_state = queue.popleft()
        for action in target["alphabet"]:
            target_next, target_output = target["transitions"][target_state][action]
            learned_next, learned_output = learned.transitions[learned_state][positions[action]]
            if target_output != learned_output: return False
            pair = (target_next, learned_next)
            if pair not in seen: seen.add(pair); queue.append(pair)
    return True


def main():
    cases = json.loads((DATA / "private_cases.json").read_text()); rows = []
    for policy in ("cold", "retain", "random_challenges", "plan_challenges"):
        summary = json.loads((RESULTS / policy / "SUMMARY.json").read_text())
        for case in cases:
            directory = RESULTS / policy / case["id"]
            target, states = product(case)
            retained = json.loads((directory / "RETAINED.json").read_text())
            artifact = inspect_artifact(directory / "ARTIFACTS" / "state.json", case)
            events = json.loads((directory / "EVENTS.json").read_text())
            task = next(row for row in summary["tasks"] if row["case"] == case["id"])
            rows.append({"policy": policy, "case": case["id"], "status": task["status"], "queries": task["queries"], "target_states": states, "artifact": artifact["matches"], "exact": exact_model(retained.get("model"), target), "replay": replay(case, events)})
    report = {"experiment": "R43", "tasks": rows, "task_count": len(rows), "artifacts": sum(r["artifact"] for r in rows), "exact": sum(r["exact"] for r in rows), "replays": sum(r["replay"] for r in rows), "goal_achieved": False}
    out = ROOT / "verification" / "R43_AUDIT.json"; out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(out), "tasks": len(rows), "artifacts": report["artifacts"], "exact": report["exact"], "replays": report["replays"]}))


if __name__ == "__main__": main()
