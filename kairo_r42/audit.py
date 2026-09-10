import hashlib
import json
import sqlite3
from pathlib import Path

from kairo_r24.backend import SQLiteTools
from kairo_r11.model import Model

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "r42"
RESULTS = ROOT / "results" / "r42"


def independent_explore(case, cap=64):
    import tempfile
    with tempfile.TemporaryDirectory(prefix="r42-audit-") as directory:
        backend = SQLiteTools(Path(directory) / "target", case)
        backend.reset()
        initial = backend.snapshot()
        snapshots = [initial]
        words = [[]]
        ids = {json.dumps(initial, sort_keys=True): "s0"}
        transitions = {}
        index = 0
        try:
            while index < len(words):
                word = words[index]
                state = "s" + str(index)
                transitions[state] = {}
                for action in sorted(case["bindings"]):
                    backend.reset()
                    for prefix in word:
                        backend.step(prefix)
                    output = backend.step(action)
                    snapshot = backend.snapshot()
                    key = json.dumps(snapshot, sort_keys=True)
                    if key not in ids:
                        if len(words) >= cap:
                            raise AssertionError("audit state cap")
                        ids[key] = "s" + str(len(words))
                        words.append(word + [action])
                        snapshots.append(snapshot)
                    transitions[state][action] = [ids[key], output]
                index += 1
            return {"initial": "s0", "alphabet": sorted(case["bindings"]), "transitions": transitions}, len(words)
        finally:
            backend.close()


def independent_replay(case, events):
    import tempfile
    with tempfile.TemporaryDirectory(prefix="r42-replay-") as directory:
        backend = SQLiteTools(Path(directory) / "replay", case)
        try:
            for event in events:
                request = event.get("request", {})
                if request.get("op") == "step":
                    expected = event["response"]["output"]
                    actual = backend.step(request["action"])
                    if actual != expected:
                        return False
            return True
        finally:
            backend.close()


def db_check(path, case):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None)
    try:
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        rows = [list(row) for row in conn.execute(f"SELECT {case['key_col']},{case['value_col']} FROM {table} ORDER BY {case['key_col']}").fetchall()]
        return table == case["table"] and rows == case["final_expected"] and conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()


def main():
    cases = json.loads((DATA / "private_cases.json").read_text())
    rows = []
    for policy in ("cold", "retain", "random_challenges", "plan_challenges"):
        summary = json.loads((RESULTS / policy / "SUMMARY.json").read_text())
        for case in cases:
            result = json.loads((RESULTS / policy / case["id"] / "RESULT.json").read_text())
            retained = json.loads((RESULTS / policy / case["id"] / "RETAINED.json").read_text())
            target, target_states = independent_explore(case)
            predicted = retained.get("model")
            exact = predicted is not None
            # Reconstruct one access word for every independently enumerated state.
            access = {"s0": []}
            changed = True
            while changed:
                changed = False
                for state, mapping in target["transitions"].items():
                    if state not in access:
                        continue
                    for action, (next_state, _) in mapping.items():
                        if next_state not in access:
                            access[next_state] = access[state] + [action]
                            changed = True
            if predicted is not None:
                learned = Model.from_dict(retained["model"])
                exact = all(list(learned.run(access[state] + [action])) == list(learned.run(access[state])) + [output] for state, mapping in target["transitions"].items() for action, (_, output) in mapping.items())
            events = json.loads((RESULTS / policy / case["id"] / "EVENTS.json").read_text())
            task = next(row for row in summary["tasks"] if row["case"] == case["id"])
            rows.append({"policy": policy, "case": case["id"], "status": task["status"], "artifact": db_check(RESULTS / policy / case["id"] / "ARTIFACTS" / "inventory.sqlite", case), "exact": bool(exact), "target_states": target_states, "replay": independent_replay(case, events), "queries": task["queries"]})
    report = {"experiment": "R42", "tasks": rows, "task_count": len(rows), "artifacts": sum(r["artifact"] for r in rows), "exact": sum(r["exact"] for r in rows), "replays": sum(r["replay"] for r in rows), "goal_achieved": False}
    out = ROOT / "verification" / "R42_AUDIT.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(out), "tasks": len(rows), "artifacts": report["artifacts"], "exact": report["exact"]}))


if __name__ == "__main__":
    main()
