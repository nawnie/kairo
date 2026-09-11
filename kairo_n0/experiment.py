"""Bounded supervised N0 training receipt using the learner-only contract."""
from __future__ import annotations

import json
import time

from kairo_r44.backprop import TraceHead

from .contract import VerifiedObservation, freeze_split, receipt, teacher_export


def observations():
    donor = [
        ("a", "zero"), ("b", "zero"), ("c", "one"), ("d", "one"),
        ("aa", "zero"), ("ab", "zero"), ("ba", "zero"), ("bb", "zero"),
    ]
    heldout = [("ca", "one"), ("da", "one"), ("cc", "one"), ("dd", "one")]
    rows = []
    for index, (word, output) in enumerate(donor):
        rows.append(VerifiedObservation("donor", f"d{index}", tuple(word), output, f"v-d{index}"))
    for index, (word, output) in enumerate(heldout):
        rows.append(VerifiedObservation("heldout", f"h{index}", tuple(word), output, f"v-h{index}"))
    return tuple(rows)


def run():
    started = time.perf_counter()
    train, heldout = freeze_split(observations(), {"heldout"})
    exported = teacher_export(train)
    head = TraceHead(["a", "b", "c", "d"], history=2, hidden_size=8, seed=5301)
    losses = head.fit([(row["prefix"], row["output"]) for row in exported], epochs=8, learning_rate=0.08)
    predictions = [head.predict(list(row.prefix)) for row in heldout]
    correct = sum(prediction["label"] == row.output for prediction, row in zip(predictions, heldout))
    result = receipt(
        {"seed": 5301, "history": 2, "hidden": 8, "epochs": 8, "observation_cap": 512},
        train, heldout, losses[0], losses[-1],
    )
    result.update({
        "heldout_correct": correct,
        "heldout_total": len(heldout),
        "heldout_accuracy": correct / len(heldout),
        "elapsed_seconds": time.perf_counter() - started,
        "network": {"input_features": head.input_size, "hidden_units": head.network.hidden_size, "output_labels": len(head.labels)},
    })
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
