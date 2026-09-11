"""Deterministic NG-RC-style temporal baselines.

This module is deliberately separate from the Kairo symbolic learner.  It
receives only sequence observations and returns predictions; it is not an
evidence source or a truth authority.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass


def _solve(a, b, ridge=1e-6):
    n = len(a)
    matrix = [[float(a[i][j]) + (ridge if i == j else 0.0) for j in range(n)] + [float(b[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(matrix[row][col]))
        if abs(matrix[pivot][col]) < 1e-12:
            raise ValueError("singular readout system")
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        scale = matrix[col][col]
        matrix[col] = [value / scale for value in matrix[col]]
        for row in range(n):
            if row == col:
                continue
            factor = matrix[row][col]
            if factor:
                matrix[row] = [x - factor * y for x, y in zip(matrix[row], matrix[col])]
    return [matrix[i][-1] for i in range(n)]


def _features(history, width, nonlinear):
    values = list(history[-width:])
    values = [0.0] * max(0, width - len(values)) + values
    features = [1.0] + values
    if nonlinear:
        features += [value * value for value in values]
        features += [values[i] * values[j] for i in range(len(values)) for j in range(i + 1, len(values))]
    return features


@dataclass
class TemporalReadout:
    width: int
    nonlinear: bool = False
    ridge: float = 1e-6
    weights: list[float] | None = None

    def fit(self, sequence, targets=None):
        rows = [_features(sequence[:index], self.width, self.nonlinear) for index in range(1, len(sequence))]
        if targets is None:
            targets = sequence
        targets = [float(targets[index]) for index in range(1, len(sequence))]
        size = len(rows[0]); gram = [[0.0] * size for _ in range(size)]; rhs = [0.0] * size
        for row, target in zip(rows, targets):
            for i, left in enumerate(row):
                rhs[i] += left * target
                for j, right in enumerate(row):
                    gram[i][j] += left * right
        self.weights = _solve(gram, rhs, self.ridge)
        return self

    def predict(self, history):
        if self.weights is None:
            raise RuntimeError("readout is not fitted")
        row = _features(history, self.width, self.nonlinear)
        return sum(weight * value for weight, value in zip(self.weights, row))

    def to_json(self):
        return {"width": self.width, "nonlinear": self.nonlinear, "ridge": self.ridge, "weights": self.weights}

    @classmethod
    def from_json(cls, value):
        return cls(value["width"], value["nonlinear"], value["ridge"], value["weights"])


def delayed_pulse(seed, length=240, delay=7):
    state = (seed * 1103515245 + 12345) & 0x7FFFFFFF; values = []
    for _ in range(length):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        values.append(1.0 if state % 7 == 0 else 0.0)
    return values, delay


def parity(seed, length=240):
    state = seed; values = []
    for _ in range(length):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        values.append(float((state >> 8) & 1))
    return values, (2, 5)


def reversal(seed, length=240):
    state = seed; values = []
    for index in range(length):
        state = (22695477 * state + 1) & 0xFFFFFFFF
        bit = float((state >> 11) & 1)
        values.append(bit if index < length // 2 else 1.0 - bit)
    return values, length // 2


def target_values(kind, sequence, metadata):
    if kind == "delayed":
        delay = metadata
        return [sequence[index - delay] if index >= delay else 0.5 for index in range(len(sequence))]
    if kind == "parity":
        left, right = metadata
        return [float(int(sequence[index - left]) ^ int(sequence[index - right])) if index >= right else 0.5 for index in range(len(sequence))]
    if kind == "reversal":
        change = metadata
        return [sequence[index] if index < change else 1.0 - sequence[index] for index in range(len(sequence))]
    raise ValueError(kind)


def evaluate(model, sequence, targets, warmup):
    errors = []
    for index in range(warmup, len(sequence)):
        prediction = model.predict(sequence[:index])
        errors.append(abs(prediction - targets[index]))
    return sum(errors) / len(errors)


def run_case(kind, seed, train_length=240, test_length=240):
    factory = {"delayed": delayed_pulse, "parity": parity, "reversal": reversal}[kind]
    train, metadata = factory(seed, train_length)
    test, test_metadata = factory(seed + 10000, test_length)
    if kind == "reversal":
        # The regime boundary is held out by using the test sequence's own
        # boundary; the learner never receives the hidden regime label.
        metadata = test_metadata = test_length // 2
    target = target_values(kind, test, test_metadata)
    train_target = target_values(kind, train, metadata)
    base = TemporalReadout(1).fit(train, train_target)
    fixed = TemporalReadout(3, nonlinear=True).fit(train, train_target)
    candidate = TemporalReadout(8, nonlinear=True).fit(train, train_target)
    return {
        "kind": kind,
        "seed": seed,
        "base_mae": evaluate(base, test, target, 8),
        "fixed_window_mae": evaluate(fixed, test, target, 8),
        "r0_ngrc_mae": evaluate(candidate, test, target, 8),
        "reload_mae": evaluate(TemporalReadout.from_json(json.loads(json.dumps(candidate.to_json()))), test, target, 8),
    }
