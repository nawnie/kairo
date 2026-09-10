import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "r43"
RESULTS = ROOT / "results" / "r43_retry"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases():
    return [
        {"id": "D1", "baseline": {"service": "billing", "version": 3, "enabled": False, "routes": ["/charge", "/refund"]}, "draft": {"service": "billing", "version": 4, "enabled": True, "routes": ["/charge", "/refund", "/void"]}, "final_expected": {"service": "billing", "version": 4, "enabled": True, "routes": ["/charge", "/refund", "/void"]}, "bindings": {"op_0": "open", "op_1": "edit", "op_2": "validate", "op_3": "inspect", "op_4": "publish", "op_5": "reload", "op_6": "rollback", "op_7": "close"}, "goal": {"require": ["draft_verified", "validation_passed", "published_verified", "session_closed"], "forbid": []}},
        {"id": "D2", "baseline": {"service": "search", "version": 11, "enabled": True, "routes": ["/query", "/suggest"]}, "draft": {"service": "search", "version": 12, "enabled": True, "routes": ["/query", "/suggest", "/semantic"]}, "final_expected": {"service": "search", "version": 12, "enabled": True, "routes": ["/query", "/suggest", "/semantic"]}, "bindings": {"op_0": "publish", "op_1": "close", "op_2": "reload", "op_3": "validate", "op_4": "open", "op_5": "inspect", "op_6": "edit", "op_7": "rollback"}, "goal": {"require": ["draft_verified", "validation_passed", "published_verified", "session_closed"], "forbid": []}},
        {"id": "D3", "baseline": {"service": "reports", "version": 8, "enabled": False, "routes": ["/daily", "/monthly", "/export"]}, "draft": {"service": "reports", "version": 9, "enabled": True, "routes": ["/daily", "/monthly", "/export", "/audit"]}, "final_expected": {"service": "reports", "version": 9, "enabled": True, "routes": ["/daily", "/monthly", "/export", "/audit"]}, "bindings": {"op_0": "inspect", "op_1": "rollback", "op_2": "edit", "op_3": "open", "op_4": "close", "op_5": "publish", "op_6": "validate", "op_7": "reload"}, "goal": {"require": ["draft_verified", "validation_passed", "published_verified", "session_closed"], "forbid": []}},
    ]


def protocol():
    value = json.loads((ROOT / "datasets" / "r40" / "PROTOCOL.json").read_text())
    value["learning"]["middle_depth"] = 2; value["learning"]["max_middle_depth"] = 2
    value["policies"] = ["cold", "retain", "random_challenges", "plan_challenges"]
    value["action_budget"] = 16; value["state_cap"] = 64
    return value


def prepare():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "PROTOCOL.json").write_text(json.dumps(protocol(), indent=2) + "\n")
    (DATA / "private_cases.json").write_text(json.dumps(cases(), indent=2) + "\n")
    freeze = {"files": {name: sha(DATA / name) for name in ("PROTOCOL.json", "private_cases.json")}, "protocol_sha256": sha(ROOT / "R24_PROTOCOL.md"), "sources": {"datasets/r23/PROTOCOL.json": sha(ROOT / "datasets" / "r23" / "PROTOCOL.json")}, "goal_achieved": False}
    (DATA / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")
    return {"cases": len(cases()), "data": str(DATA), "source_hashes": freeze["sources"]}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("prepare", "run")); parser.add_argument("--policy")
    args = parser.parse_args(); prepare()
    if args.command == "run":
        policies = [args.policy] if args.policy else protocol()["policies"]
        for policy in policies:
            subprocess.run([sys.executable, "-m", "kairo_r43.benchmark", "--policy", policy, "--output", str(RESULTS / policy)], cwd=ROOT, check=True)
    else:
        print(json.dumps(prepare(), sort_keys=True))


if __name__ == "__main__": main()
