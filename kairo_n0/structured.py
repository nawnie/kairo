"""Small binding-invariant neural representation for the next N0/N1 probe."""
from __future__ import annotations

import itertools

from kairo_r44.backprop import MLP


def canonical_pattern(word, history=3):
    names = {}; pattern = []
    for action in list(word)[-history:]:
        if action not in names:
            names[action] = len(names)
        pattern.append(str(names[action]))
    return "".join(pattern)


def pattern_vocabulary(history=3):
    values = {""}
    for length in range(1, history + 1):
        for word in itertools.product(range(length), repeat=length):
            if word[0] != 0 or any(value > max(word[:index]) + 1 for index, value in enumerate(word[1:], 1)):
                continue
            values.add("".join(str(value) for value in word))
    return tuple(sorted(values, key=lambda value: (len(value), value)))


class PatternHead:
    """MLP over canonical first-occurrence patterns, not action identities."""

    def __init__(self, history=3, hidden_size=8, seed=5401):
        self.history = history; self.vocabulary = pattern_vocabulary(history); self.labels = ()
        self.hidden_size = hidden_size
        self.network = None; self.seed = seed; self.input_size = len(self.vocabulary) + 1

    def encode(self, word):
        vector = [0.0] * self.input_size
        pattern = canonical_pattern(word, self.history)
        vector[self.vocabulary.index(pattern)] = 1.0
        vector[-1] = min(len(word), self.history) / self.history
        return vector

    def fit(self, observations, epochs=8, learning_rate=0.08):
        self.labels = tuple(sorted({output for _, output in observations}))
        self.network = MLP(self.input_size, self.hidden_size, len(self.labels), self.seed)
        samples = [self.encode(word) for word, _ in observations]
        labels = [self.labels.index(output) for _, output in observations]
        return self.network.train(samples, labels, epochs, learning_rate)

    def predict(self, word):
        probabilities = self.network.probabilities(self.encode(word))
        index = max(range(len(probabilities)), key=probabilities.__getitem__)
        return {"label": self.labels[index], "confidence": probabilities[index]}
