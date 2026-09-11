import json
from pathlib import Path

from kairo_r43.audit import product, replay, exact_model
from kairo_r43.experiment import cases

ROOT = Path(__file__).resolve().parents[1]; RESULTS = ROOT / "results" / "r54_retry3"
POLICIES = ("random_challenges", "backprop_challenges", "structured_backprop_challenges")


def main():
    rows = []
    for policy in POLICIES:
        summary = json.loads((RESULTS / policy / "SUMMARY.json").read_text())
        for case in cases():
            directory = RESULTS / policy / case["id"]; target, states = product(case)
            retained = json.loads((directory / "RETAINED.json").read_text())
            artifact = json.loads((directory / "ARTIFACTS" / "state.json").read_text())
            events = json.loads((directory / "EVENTS.json").read_text())
            task = next(row for row in summary["tasks"] if row["case"] == case["id"])
            rows.append({"policy": policy, "case": case["id"], "status": task["status"], "queries": task["queries"], "artifact": artifact == case["final_expected"], "exact": exact_model(retained.get("model"), target), "replay": replay(case, events), "target_states": states})
    report = {"experiment": "R54", "tasks": rows, "task_count": len(rows), "artifacts": sum(row["artifact"] for row in rows), "exact": sum(row["exact"] for row in rows), "replays": sum(row["replay"] for row in rows), "goal_achieved": False}
    out = ROOT / "verification" / "R54_AUDIT.json"; out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(out), "tasks": len(rows), "artifacts": report["artifacts"], "exact": report["exact"], "replays": report["replays"]}))


if __name__ == "__main__":
    main()
