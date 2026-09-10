import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "r42"
RESULTS = ROOT / "results" / "r42"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases():
    return [
        {
            "id": "S1", "table": "orders", "key_col": "order_id", "value_col": "units",
            "baseline": [["o-11", 40], ["o-22", 90], ["o-33", 150], ["o-44", 260]],
            "expected": [["o-11", 37], ["o-22", 84], ["o-33", 141], ["o-44", 248]],
            "final_expected": [["o-11", 37], ["o-22", 84], ["o-33", 141], ["o-44", 248]],
            "bindings": {"op_0": "open", "op_1": "begin", "op_2": "stage", "op_3": "savepoint", "op_4": "rollback_to_savepoint", "op_5": "inspect", "op_6": "commit", "op_7": "close"},
            "goal": {"require": ["pending_verified", "rollback_to_savepoint", "durable_verified", "session_closed"], "forbid": []},
        },
        {
            "id": "S2", "table": "ledger_lines", "key_col": "line_id", "value_col": "amount",
            "baseline": [["l-a", 1000], ["l-b", 2300], ["l-c", 7800], ["l-d", 12000], ["l-e", 19900]],
            "expected": [["l-a", 991], ["l-b", 2278], ["l-c", 7737], ["l-d", 11944], ["l-e", 19825]],
            "final_expected": [["l-a", 991], ["l-b", 2278], ["l-c", 7737], ["l-d", 11944], ["l-e", 19825]],
            "bindings": {"op_0": "savepoint", "op_1": "commit", "op_2": "close", "op_3": "inspect", "op_4": "stage", "op_5": "open", "op_6": "rollback_to_savepoint", "op_7": "begin"},
            "goal": {"require": ["pending_verified", "rollback_to_savepoint", "durable_verified", "session_closed"], "forbid": []},
        },
        {
            "id": "S3", "table": "telemetry", "key_col": "sample_id", "value_col": "reading",
            "baseline": [["t01", 17], ["t02", 28], ["t03", 39], ["t04", 50], ["t05", 61], ["t06", 72]],
            "expected": [["t01", 16], ["t02", 26], ["t03", 36], ["t04", 46], ["t05", 56], ["t06", 66]],
            "final_expected": [["t01", 16], ["t02", 26], ["t03", 36], ["t04", 46], ["t05", 56], ["t06", 66]],
            "bindings": {"op_0": "inspect", "op_1": "rollback_to_savepoint", "op_2": "begin", "op_3": "close", "op_4": "commit", "op_5": "open", "op_6": "savepoint", "op_7": "stage"},
            "goal": {"require": ["pending_verified", "rollback_to_savepoint", "durable_verified", "session_closed"], "forbid": []},
        },
    ]


def protocol():
    value = json.loads((ROOT / "datasets" / "r40" / "PROTOCOL.json").read_text())
    value["learning"]["middle_depth"] = 2
    value["learning"]["max_middle_depth"] = 2
    value["policies"] = ["cold", "retain", "random_challenges", "plan_challenges"]
    value["action_budget"] = 16
    value["state_cap"] = 64
    return value


def prepare():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "PROTOCOL.json").write_text(json.dumps(protocol(), indent=2) + "\n")
    (DATA / "private_cases.json").write_text(json.dumps(cases(), indent=2) + "\n")
    freeze = {
        "files": {name: sha(DATA / name) for name in ("PROTOCOL.json", "private_cases.json")},
        "protocol_sha256": sha(ROOT / "R24_PROTOCOL.md"),
        "sources": {"datasets/r23/PROTOCOL.json": sha(ROOT / "datasets" / "r23" / "PROTOCOL.json")},
        "goal_achieved": False,
    }
    (DATA / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")
    return {"data": str(DATA), "cases": len(cases()), "source": freeze["sources"]}


def run(policy, output):
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "kairo_r24.benchmark", "--policy", policy, "--output", str(output), "--data-dir", "datasets/r42"]
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--policy")
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare(), sort_keys=True))
        return
    prepare()
    if args.policy:
        run(args.policy, RESULTS / args.policy)
    else:
        for policy in protocol()["policies"]:
            run(policy, RESULTS / policy)


if __name__ == "__main__":
    main()
