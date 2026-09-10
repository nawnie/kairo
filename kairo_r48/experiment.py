import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from kairo_r43.experiment import cases

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "datasets" / "r48"; RESULTS = ROOT / "results" / "r48"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def protocol():
    value = json.loads((ROOT / "datasets" / "r40" / "PROTOCOL.json").read_text())
    value["learning"]["middle_depth"] = 1; value["learning"]["max_middle_depth"] = 2
    value["policies"] = ["plan_challenges", "random_challenges", "backprop_challenges"]
    value["action_budget"] = 16; value["state_cap"] = 64
    return value


def prepare():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "PROTOCOL.json").write_text(json.dumps(protocol(), indent=2) + "\n")
    (DATA / "private_cases.json").write_text(json.dumps(cases(), indent=2) + "\n")
    freeze = {"files": {name: sha(DATA / name) for name in ("PROTOCOL.json", "private_cases.json")}, "protocol_sha256": sha(ROOT / "R24_PROTOCOL.md"), "sources": {"datasets/r23/PROTOCOL.json": sha(ROOT / "datasets" / "r23" / "PROTOCOL.json")}, "goal_achieved": False}
    (DATA / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")
    return {"cases": len(cases()), "policies": protocol()["policies"], "middle_depth": 1, "max_middle_depth": 2}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("prepare", "run")); args = parser.parse_args(); info = prepare()
    if args.command == "prepare": print(json.dumps(info, sort_keys=True)); return
    for policy in protocol()["policies"]:
        subprocess.run([sys.executable, "-m", "kairo_r43.benchmark", "--policy", policy, "--output", str(RESULTS / policy), "--data-dir", "datasets/r48"], cwd=ROOT, check=True)


if __name__ == "__main__": main()
