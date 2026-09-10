"""Backprop-ranked challenge policy using only observed query traces."""
import json
import sys

from kairo_r11.model import Model
from kairo_r12.transfer import select_seeds
from kairo_r15.client import digest
from kairo_r18.feedback import FeedbackLearner
from kairo_r19.client import satisfies
from kairo_r22.file_client import run as task_run
from kairo_r23.challenges import edits
from .backprop import TraceHead


def run(boot, call):
    protocol = boot["protocol"]; observations = []; observation_cap = 512; observations_seen = 0; reservoir_state = 44017 + boot["ordinal"]

    def remember(pair):
        nonlocal observations_seen, reservoir_state
        observations_seen += 1
        if len(observations) < observation_cap:
            observations.append(pair); return
        reservoir_state = (1664525 * reservoir_state + 1013904223) & 0xFFFFFFFF
        slot = reservoir_state % observations_seen
        if slot < observation_cap: observations[slot] = pair

    def observed_call(request):
        response = call(request)
        if request.get("op") == "query":
            word = list(request["word"])
            outputs = list(response["outputs"])
            for index, output in enumerate(outputs): remember((word[:index], output))
        return response

    base = task_run({**boot, "policy": "retained_model", "memory": None}, observed_call)
    call({"op": "task_checkpoint"})
    artifact = base["retained"]; checks = []; mismatches = []; repair = None; validation = None
    queries = base["queries"]; symbols = base["input_symbols"]; model_status = "not_challenged"
    word = [row["action"] for row in base["actions"]]
    def query(value, purpose):
        nonlocal queries, symbols
        result = call({"op": "query", "word": list(value), "purpose": purpose})["outputs"]
        queries += 1; symbols += len(value); return result

    head = TraceHead(boot["alphabet"], seed=4401 + boot["ordinal"])
    training_losses = head.fit(observations, epochs=8) if observations else []
    if base["status"] == "success" and artifact and artifact["model"]:
        model = Model.from_dict(artifact["model"])
        generated = edits(word, protocol["challenge_queries"], protocol["action_budget"])
        ranked = []
        for proposal in generated:
            scored = dict(proposal); scored["backprop_uncertainty"] = head.challenge_score(proposal["word"])
            ranked.append(scored)
        ranked.sort(key=lambda row: (-row["backprop_uncertainty"], row["word"]))
        for proposal in ranked:
            value = proposal["word"]; observed = query(value, "challenge"); predicted = list(model.run(value))
            mismatch = observed != predicted
            checks.append({**proposal, "observed": observed, "predicted": predicted, "mismatch": mismatch})
            if mismatch: mismatches.append(value)
        model_status = "not_refuted_by_backprop_ranked_challenges" if generated else model_status
        if mismatches:
            model_status = "refuted_repair_failed"
            donor = {key: artifact[key] for key in ("access_words", "distinguishing_suffixes")}; donor.update(alphabet=artifact["model"]["alphabet"], learning_sha256=digest(artifact))
            seeds = select_seeds({"donors": [donor]}, boot["alphabet"], "learned_table", protocol["learning"]["control_seed"])
            call({"op": "begin_acquisition"})
            learner = FeedbackLearner(boot["alphabet"], lambda value: query(value, "acquisition"), protocol["learning"], seeds, protocol["screening_query_budget"], mismatches)
            repair = learner.run(); call({"op": "end_acquisition", "queries": repair["queries"], "symbols": repair["input_symbols"]}); artifact = None
            if repair["model"] and repair["task_feedback"]["all_consistent"]:
                observed = query(word, "validation"); predicted = list(Model.from_dict(repair["model"]).run(word)); accepted = observed == predicted and satisfies(boot["goal"], observed)
                validation = {"word": word, "observed": observed, "predicted": predicted, "accepted": accepted}
                if accepted: artifact = repair; model_status = "repaired_against_observed_feedback"
    return {"policy": boot["policy"], "status": base["status"], "base": base, "challenges": checks, "mismatching_words": mismatches, "repair": repair, "repair_validation": validation, "model_status": model_status, "retained": artifact, "queries": queries, "input_symbols": symbols, "actions": base["actions"], "backprop": {"observations": len(observations), "observations_seen": observations_seen, "observation_cap": observation_cap, "labels": list(head.labels), "epochs": len(training_losses), "initial_loss": training_losses[0] if training_losses else None, "final_loss": training_losses[-1] if training_losses else None}}


if __name__ == "__main__":
    boot = json.loads(sys.stdin.readline())
    def call(request):
        print(json.dumps(request), flush=True); return json.loads(sys.stdin.readline())
    print(json.dumps({"op": "result", "result": run(boot, call)}), flush=True)
