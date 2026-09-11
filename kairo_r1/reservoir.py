"""Small deterministic leaky recurrent reservoir with ridge readout."""
from __future__ import annotations

import math


def _rng(seed):
    state = seed & 0xFFFFFFFF
    while True:
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        yield state / 0xFFFFFFFF


def _solve(a, b, ridge=1e-5):
    n = len(a); matrix = [[float(a[i][j]) + (ridge if i == j else 0.0) for j in range(n)] + [float(b[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(matrix[row][col]))
        if abs(matrix[pivot][col]) < 1e-12: raise ValueError("singular readout system")
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        scale = matrix[col][col]; matrix[col] = [value / scale for value in matrix[col]]
        for row in range(n):
            if row == col: continue
            factor = matrix[row][col]
            if factor: matrix[row] = [x - factor * y for x, y in zip(matrix[row], matrix[col])]
    return [matrix[i][-1] for i in range(n)]


class ReservoirReadout:
    """x_t=(1-leak)x_prev+leak*tanh(W_res*x_prev+W_in*u_t+b)."""

    def __init__(self, size=24, leak=0.4, density=0.2, seed=5801, ridge=1e-5):
        if size <= 0 or not 0.0 < leak <= 1.0 or not 0.0 < density <= 1.0: raise ValueError("invalid reservoir configuration")
        self.size = size; self.leak = leak; self.density = density; self.seed = seed; self.ridge = ridge; self.state = [0.0] * size
        generator = _rng(seed)
        self.input_weights = [next(generator) * 1.0 - 0.5 for _ in range(size)]
        self.bias = [next(generator) * 0.2 - 0.1 for _ in range(size)]
        self.recurrent = []
        for _ in range(size):
            row = []
            for _ in range(size):
                row.append((next(generator) * 2.0 - 1.0) * 0.55 if next(generator) < density else 0.0)
            self.recurrent.append(row)
        self.weights = None

    def reset(self):
        self.state = [0.0] * self.size

    def _step(self, value):
        previous = self.state
        self.state = [
            (1.0 - self.leak) * previous[index] + self.leak * math.tanh(
                sum(weight * old for weight, old in zip(row, previous)) + input_weight * value + bias
            ) for index, (row, input_weight, bias) in enumerate(zip(self.recurrent, self.input_weights, self.bias))
        ]
        return [1.0] + list(self.state)

    def fit(self, sequence, targets, washout=16):
        if len(sequence) != len(targets) or len(sequence) <= washout: raise ValueError("training sequence mismatch")
        self.reset(); rows = []
        for index, value in enumerate(sequence):
            features = self._step(value)
            if index >= washout: rows.append((features, float(targets[index])))
        width = self.size + 1; gram = [[0.0] * width for _ in range(width)]; rhs = [0.0] * width
        for row, target in rows:
            for i, left in enumerate(row):
                rhs[i] += left * target
                for j, right in enumerate(row): gram[i][j] += left * right
        self.weights = _solve(gram, rhs, self.ridge); return self

    def predict_sequence(self, sequence):
        if self.weights is None: raise RuntimeError("reservoir is not fitted")
        self.reset(); outputs = []
        for value in sequence:
            features = self._step(value); outputs.append(sum(weight * feature for weight, feature in zip(self.weights, features)))
        return outputs

    def to_json(self):
        return {"size": self.size, "leak": self.leak, "density": self.density, "seed": self.seed, "ridge": self.ridge, "input_weights": self.input_weights, "bias": self.bias, "recurrent": self.recurrent, "weights": self.weights}

    @classmethod
    def from_json(cls, value):
        result = cls(value["size"], value["leak"], value["density"], value["seed"], value["ridge"])
        result.input_weights = value["input_weights"]; result.bias = value["bias"]; result.recurrent = value["recurrent"]; result.weights = value["weights"]
        return result
