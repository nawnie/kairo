from __future__ import annotations

import json
import time
import tracemalloc
import ctypes
from ctypes import wintypes
from pathlib import Path

from kairo_r0.temporal import TemporalReadout, evaluate
from kairo_r1.reservoir import ReservoirReadout


def sequence(kind, seed, length, metadata):
    state = seed; values = []
    for index in range(length):
        if kind == "delayed":
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF; values.append(1.0 if state % 7 == 0 else 0.0)
        elif kind == "parity":
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF; values.append(float((state >> 8) & 1))
        elif kind == "reversal":
            state = (22695477 * state + 1) & 0xFFFFFFFF; bit = float((state >> 11) & 1); values.append(bit if index < metadata else 1.0 - bit)
        else: raise ValueError(kind)
    return values


def targets(kind, values, metadata):
    if kind == "delayed": return [values[index - metadata] if index >= metadata else 0.5 for index in range(len(values))]
    if kind == "parity":
        left, right = metadata; return [float(int(values[index - left]) ^ int(values[index - right])) if index >= right else 0.5 for index in range(len(values))]
    if kind == "reversal": return [values[index] if index < metadata else 1.0 - values[index] for index in range(len(values))]
    raise ValueError(kind)


CONFIGS = (
    ("delayed_3", "delayed", 3, 3),
    ("delayed_7", "delayed", 7, 7),
    ("parity_2_5", "parity", (2, 5), (2, 5)),
    ("parity_3_7", "parity", (3, 7), (3, 7)),
    ("reversal_mid", "reversal", 160, 160),
    ("unseen_delay", "delayed", 3, 7),
)
SEEDS = (11, 17, 23, 29, 31)


class _MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("page_fault_count", wintypes.DWORD), ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t), ("quota_peak_paged_pool_usage", ctypes.c_size_t), ("quota_paged_pool_usage", ctypes.c_size_t), ("quota_peak_non_paged_pool_usage", ctypes.c_size_t), ("quota_non_paged_pool_usage", ctypes.c_size_t), ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t)]


def peak_working_set():
    counters = _MemoryCounters(); counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.windll.kernel32; psapi = ctypes.windll.psapi
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MemoryCounters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return 0
    return int(counters.peak_working_set_size)


def reservoir_mae(model, sequence_value, target, warmup=16):
    predictions = model.predict_sequence(sequence_value)
    errors = [abs(predictions[index] - target[index]) for index in range(warmup, len(target))]
    return sum(errors) / len(errors)


def run_case(name, kind, train_meta, test_meta, seed):
    started = time.perf_counter(); tracemalloc.start()
    train = sequence(kind, seed, 320, train_meta); test = sequence(kind, seed + 10000, 320, test_meta)
    train_targets = targets(kind, train, train_meta); test_targets = targets(kind, test, test_meta)
    base = TemporalReadout(1).fit(train, train_targets); fixed = TemporalReadout(3, nonlinear=True).fit(train, train_targets)
    reservoir = ReservoirReadout(size=24, leak=0.4, density=0.2, seed=5801 + seed).fit(train, train_targets, washout=16)
    restored = ReservoirReadout.from_json(json.loads(json.dumps(reservoir.to_json())))
    result = {"config": name, "seed": seed,
              "base_mae": evaluate(base, test, test_targets, 16),
              "fixed_window_mae": evaluate(fixed, test, test_targets, 16),
              "reservoir_mae": reservoir_mae(reservoir, test, test_targets),
              "reload_mae": reservoir_mae(restored, test, test_targets),
              "elapsed_seconds": time.perf_counter() - started}
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop(); result["peak_python_bytes"] = peak; result["peak_rss_bytes"] = peak_working_set()
    return result


def run():
    rows = [run_case(name, kind, train_meta, test_meta, seed) for name, kind, train_meta, test_meta in CONFIGS for seed in SEEDS]
    return {"experiment": "R58-R1-recurrent-reservoir", "rows": rows, "case_count": len(rows),
            "reservoir_wins_fixed": sum(row["reservoir_mae"] < row["fixed_window_mae"] for row in rows),
            "reservoir_matches_or_beats_base": sum(row["reservoir_mae"] <= row["base_mae"] for row in rows),
            "reload_exact": all(row["reservoir_mae"] == row["reload_mae"] for row in rows),
            "goal_achieved": False}


if __name__ == "__main__":
    output = run(); path = Path("verification/R58_R1.json"); path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(output, indent=2) + "\n"); print(json.dumps({key: output[key] for key in ("experiment", "case_count", "reservoir_wins_fixed", "reservoir_matches_or_beats_base", "reload_exact")}, sort_keys=True))
