from __future__ import annotations

import json
import statistics
from pathlib import Path

from kairo_r0.temporal import TemporalReadout


SEEDS = (11, 17, 23, 29, 31)
CONFIGS = (("delayed_3", "delayed", 3), ("delayed_7", "delayed", 7), ("parity_2_5", "parity", (2, 5)), ("parity_3_7", "parity", (3, 7)), ("reversal_mid", "reversal", 160))
WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)


def sequence(kind, seed, length, metadata):
    state = seed; values = []
    for index in range(length):
        if kind == "delayed": state = (state * 1103515245 + 12345) & 0x7FFFFFFF; values.append(1.0 if state % 7 == 0 else 0.0)
        elif kind == "parity": state = (1664525 * state + 1013904223) & 0xFFFFFFFF; values.append(float((state >> 8) & 1))
        else: state = (22695477 * state + 1) & 0xFFFFFFFF; bit = float((state >> 11) & 1); values.append(bit if index < metadata else 1.0 - bit)
    return values


def targets(kind, values, metadata):
    if kind == "delayed": return [values[i - metadata] if i >= metadata else 0.5 for i in range(len(values))]
    if kind == "parity": return [float(int(values[i - metadata[0]]) ^ int(values[i - metadata[1]])) if i >= metadata[1] else 0.5 for i in range(len(values))]
    return [values[i] if i < metadata else 1.0 - values[i] for i in range(len(values))]


def predictions(model, sequence_value):
    return [model.predict(sequence_value[:index]) for index in range(len(sequence_value))]


def run():
    rows = []
    for name, kind, metadata in CONFIGS:
        for seed in SEEDS:
            train = sequence(kind, seed, 320, metadata); test = sequence(kind, seed + 10000, 320, metadata)
            train_targets = targets(kind, train, metadata); test_targets = targets(kind, test, metadata)
            fixed = TemporalReadout(3, nonlinear=True).fit(train, train_targets); r0 = TemporalReadout(8, nonlinear=True).fit(train, train_targets)
            fixed_predictions = predictions(fixed, test); r0_predictions = predictions(r0, test)
            for weight in WEIGHTS:
                errors = [abs(((1.0 - weight) * fixed_predictions[i] + weight * r0_predictions[i]) - test_targets[i]) for i in range(16, len(test))]
                rows.append({"config": name, "seed": seed, "weight": weight, "mae": sum(errors) / len(errors)})
    means = {str(weight): statistics.mean(row["mae"] for row in rows if row["weight"] == weight) for weight in WEIGHTS}
    return {"experiment": "R60-R0-weight-sweep", "rows": rows, "case_count": len(rows), "mean_mae_by_weight": means, "best_weight": min(WEIGHTS, key=lambda weight: means[str(weight)]), "goal_achieved": False}


if __name__ == "__main__":
    result = run(); path = Path("verification/R60_R0_WEIGHT.json"); path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(result, indent=2) + "\n"); print(json.dumps({key: result[key] for key in ("experiment", "case_count", "mean_mae_by_weight", "best_weight")}, sort_keys=True))
