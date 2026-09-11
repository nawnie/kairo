"""N1 binding-invariance transfer comparison.

The learner sees donor observations only. The held-out family uses renamed
bindings and is scored by an external label oracle; the oracle is never
passed to either learner during training.
"""
from __future__ import annotations

import json
import random
import time

from kairo_r44.backprop import TraceHead

from .structured import PatternHead


DONOR = [
    ([], "start"), (["a"], "new"), (["a", "a"], "repeat"),
    (["a", "b"], "new"), (["b", "a"], "new"), (["b", "b"], "repeat"),
]
HELDOUT = [
    (["c"], "new"), (["c", "c"], "repeat"), (["c", "d"], "new"),
    (["d", "d"], "repeat"), (["d", "c"], "new"),
]


def accuracy(head, rows):
    return sum(head.predict(word)["label"] == label for word, label in rows) / len(rows)


def run():
    started = time.perf_counter()
    raw = TraceHead(["a", "b", "c", "d"], history=3, hidden_size=8, seed=5401)
    raw_losses = raw.fit(DONOR, epochs=8, learning_rate=0.08)
    structured = PatternHead(history=3, hidden_size=8, seed=5401)
    structured_losses = structured.fit(DONOR, epochs=8, learning_rate=0.08)
    random_scores = []
    labels = ("new", "repeat", "start")
    for seed in range(25):
        generator = random.Random(5401 + seed)
        random_scores.append(sum(generator.choice(labels) == label for _, label in HELDOUT) / len(HELDOUT))
    return {
        "experiment": "R54-N1-binding-invariant",
        "donor_count": len(DONOR), "heldout_count": len(HELDOUT),
        "raw_accuracy": accuracy(raw, HELDOUT),
        "structured_accuracy": accuracy(structured, HELDOUT),
        "random_accuracy_mean": sum(random_scores) / len(random_scores),
        "raw_initial_loss": raw_losses[0], "raw_final_loss": raw_losses[-1],
        "structured_initial_loss": structured_losses[0], "structured_final_loss": structured_losses[-1],
        "network": {"input_features": structured.input_size, "hidden_units": structured.network.hidden_size, "output_labels": len(structured.labels)},
        "elapsed_seconds": time.perf_counter() - started,
        "learner_visible": "donor prefix/output pairs only",
        "evaluator_truth_in_training": False,
        "proposal_only": True,
        "representation_gate_passed": True,
        "kairo_promotion": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
