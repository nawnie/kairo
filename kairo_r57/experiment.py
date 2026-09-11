from __future__ import annotations

import json
import time
import tracemalloc
from pathlib import Path

from kairo_r0.temporal import TemporalReadout, evaluate


def sequence(kind, seed, length, metadata):
    state = seed; values = []
    for index in range(length):
        if kind == "delayed":
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF; values.append(1.0 if state % 7 == 0 else 0.0)
        elif kind == "parity":
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF; values.append(float((state >> 8) & 1))
        elif kind == "reversal":
            state = (22695477 * state + 1) & 0xFFFFFFFF; bit = float((state >> 11) & 1); values.append(bit if index < metadata else 1.0 - bit)
        else:
            raise ValueError(kind)
    return values


def targets(kind, values, metadata):
    if kind == "delayed":
        return [values[index - metadata] if index >= metadata else 0.5 for index in range(len(values))]
    if kind == "parity":
        left, right = metadata
        return [float(int(values[index - left]) ^ int(values[index - right])) if index >= right else 0.5 for index in range(len(values))]
    if kind == "reversal":
        return [values[index] if index < metadata else 1.0 - values[index] for index in range(len(values))]
    raise ValueError(kind)


CONFIGS = (
    ("delayed_3", "delayed", 3),
    ("delayed_7", "delayed", 7),
    ("parity_2_5", "parity", (2, 5)),
    ("parity_3_7", "parity", (3, 7)),
    ("reversal_mid", "reversal", 160),
)
SEEDS = (11, 17, 23, 29, 31)


def run_case(name, kind, metadata, seed):
    started = time.perf_counter(); tracemalloc.start()
    train = sequence(kind, seed, 320, metadata); test = sequence(kind, seed + 10000, 320, metadata)
    train_targets = targets(kind, train, metadata); test_targets = targets(kind, test, metadata)
    base = TemporalReadout(1).fit(train, train_targets)
    fixed = TemporalReadout(3, nonlinear=True).fit(train, train_targets)
    candidate = TemporalReadout(8, nonlinear=True).fit(train, train_targets)
    restored = TemporalReadout.from_json(json.loads(json.dumps(candidate.to_json())))
    result = {"config": name, "kind": kind, "metadata": metadata, "seed": seed,
              "base_mae": evaluate(base, test, test_targets, 8),
              "fixed_window_mae": evaluate(fixed, test, test_targets, 8),
              "r0_mae": evaluate(candidate, test, test_targets, 8),
              "reload_mae": evaluate(restored, test, test_targets, 8),
              "elapsed_seconds": time.perf_counter() - started}
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop(); result["peak_python_bytes"] = peak
    return result


def run():
    rows = [run_case(name, kind, metadata, seed) for name, kind, metadata in CONFIGS for seed in SEEDS]
    return {"experiment": "R57-R0-broader", "rows": rows, "case_count": len(rows),
            "r0_wins_fixed": sum(row["r0_mae"] < row["fixed_window_mae"] for row in rows),
            "r0_matches_or_beats_base": sum(row["r0_mae"] <= row["base_mae"] for row in rows),
            "reload_exact": all(row["r0_mae"] == row["reload_mae"] for row in rows),
            "goal_achieved": False}


if __name__ == "__main__":
    output = run(); path = Path("verification/R57_R0.json"); path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(output, indent=2) + "\n"); print(json.dumps({key: output[key] for key in ("experiment", "case_count", "r0_wins_fixed", "r0_matches_or_beats_base", "reload_exact")}, sort_keys=True))
