import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from kairo_r43.experiment import cases as source_cases

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "datasets" / "r55"; RESULTS = ROOT / "results" / "r55_retry"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    DATA.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((ROOT / "datasets" / "r40" / "PROTOCOL.json").read_text())
    protocol["learning"]["middle_depth"] = 1; protocol["learning"]["max_middle_depth"] = 1
    protocol["policies"] = ["earlystop_random_challenges", "earlystop_backprop_challenges", "earlystop_structured_backprop_challenges"]
    protocol["action_budget"] = 12; protocol["state_cap"] = 32
    (DATA / "PROTOCOL.json").write_text(json.dumps(protocol, indent=2) + "\n")
    (DATA / "private_cases.json").write_text(json.dumps(source_cases(), indent=2) + "\n")
    freeze = {"files": {name: sha(DATA / name) for name in ("PROTOCOL.json", "private_cases.json")}, "protocol_sha256": sha(ROOT / "R24_PROTOCOL.md"), "sources": {"datasets/r23/PROTOCOL.json": sha(ROOT / "datasets" / "r23" / "PROTOCOL.json")}, "goal_achieved": False}
    (DATA / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")
    return {"cases": len(source_cases()), "policies": protocol["policies"]}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("prepare", "run")); args = parser.parse_args(); info = prepare()
    if args.command == "prepare": print(json.dumps(info, sort_keys=True)); return
    for policy in info["policies"]:
        subprocess.run([sys.executable, "-m", "kairo_r43.benchmark", "--policy", policy, "--output", str(RESULTS / policy), "--data-dir", "datasets/r55"], cwd=ROOT, check=True)


if __name__ == "__main__": main()
