import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from kairo_r11.benchmark import write
from kairo_r11.reference import equivalence
from kairo_r12.benchmark import sha
from kairo_r23.host import Host
from kairo_r23.process import child
from kairo_r24.backend import explore
from .backend import FileWorkflow, inspect_artifact


def frozen(root, data):
    load = lambda name: json.loads((data / name).read_text())
    freeze = load("FREEZE.json")
    assert sha(root / "R24_PROTOCOL.md") == freeze["protocol_sha256"]
    assert all(sha(data / name) == value for name, value in freeze["files"].items())
    assert all(sha(root / name) == value for name, value in freeze["sources"].items())
    return data, load


def finalize(host, dest, case):
    checkpoint = host.actual.snapshot()
    disk = host.actual.disk_hash()
    if host.checkpoint is not None:
        assert checkpoint == host.checkpoint
    io = {"probe": dict(host.probe.meters), "execution": dict(host.actual.meters), "checkpoint": checkpoint,
          "checkpoint_disk_sha256": disk}
    host.actual.close(); host.probe.close()
    artifacts = dest / "ARTIFACTS"; artifacts.mkdir()
    shutil.copyfile(host.actual.path, artifacts / "state.json")
    observed = inspect_artifact(artifacts / "state.json", case)
    io.update(artifact_sha256=sha(artifacts / "state.json"), independent_artifact_read=observed,
              persisted_expected_match=observed["matches"], checkpoint_present=host.checkpoint is not None)
    write(dest / "FILE_IO.json", io)
    return io


def run(root, out, policy, data_dir="datasets/r43"):
    data, load = frozen(root, root / data_dir)
    protocol = load("PROTOCOL.json")
    assert policy in protocol["policies"]
    artifact = None; rows = []
    for ordinal, case in enumerate(load("private_cases.json")):
        dest = out / case["id"]
        boot = {"policy": "cold_model" if policy == "cold" else policy, "protocol": protocol,
                "alphabet": sorted(case["bindings"]), "ordinal": ordinal, "goal": case["goal"],
                "retained": None if policy == "cold" else artifact}
        with tempfile.TemporaryDirectory(prefix="kairo_r43_file_") as directory:
            make = lambda name: FileWorkflow(Path(directory) / name, case)
            host = Host(make("probe"), make("actual"), protocol)
            old_handle = host.handle; checkpoint_hash = []
            def handle(request):
                response = old_handle(request)
                if request["op"] == "task_checkpoint": checkpoint_hash.append(host.actual.disk_hash())
                return response
            host.handle = handle
            entry = "kairo_r22.file_client" if policy == "cold" else ("kairo_r44.client" if policy in ("backprop_challenges", "frontier_backprop") else "kairo_r23.client")
            result = child(root, dest, boot, host, entry)
            assert result["queries"] == host.queries and result["input_symbols"] == host.symbols and not host.acquiring
            if checkpoint_hash: assert checkpoint_hash == [host.actual.disk_hash()]
            io = finalize(host, dest, case)
            evaluation = explore(make("evaluator"), protocol["state_cap"])
            target = evaluation["model"]
            def compare(value):
                return equivalence(target, value["model"]) if target and value and value.get("model") else None
            before = result["retained"] if policy == "cold" else result["base"]["retained"]
            evaluation.update(incoming_equivalence=compare(boot["retained"]), before_challenges_equivalence=compare(before), final_equivalence=compare(result["retained"]))
            write(dest / "EVALUATION.json", evaluation)
            write(dest / "EVENTS.json", host.events)
        write(dest / "RETAINED.json", result["retained"])
        row = {"case": case["id"], "policy": policy, "status": result["status"], "artifact_verified": io["persisted_expected_match"],
               "queries": host.queries, "input_symbols": host.symbols, "acquisition_queries": host.aq,
               "challenge_queries": host.cq, "validation_queries": host.dq, "execution_actions": host.steps,
               "mismatches": len(result.get("mismatching_words", [])), "final_equivalent": evaluation["final_equivalence"]["equivalent"] if evaluation["final_equivalence"] else None}
        write(dest / "SUMMARY.json", row); rows.append(row); print(json.dumps(row), flush=True)
    summary = {"policy": policy, "tasks": rows, "successes": sum(r["status"] == "success" and r["artifact_verified"] for r in rows),
               "exact_models": sum(r["final_equivalent"] is True for r in rows), "goal_achieved": False,
               "queries": sum(r["queries"] for r in rows), "input_symbols": sum(r["input_symbols"] for r in rows),
               "execution_actions": sum(r["execution_actions"] for r in rows)}
    write(out / "SUMMARY.json", summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--policy", required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--data-dir", default="datasets/r43")
    args = parser.parse_args(); run(Path.cwd(), args.output, args.policy, args.data_dir)
