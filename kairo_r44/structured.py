"""Child-process-local canonicalized N1 proposal head."""
import itertools

from .backprop import MLP


def canonical_pattern(word, history=6):
    names = {}; pattern = []
    for action in list(word)[-history:]:
        if action not in names:
            names[action] = len(names)
        pattern.append(str(names[action]))
    return "".join(pattern)


def pattern_vocabulary(history=6):
    values = {""}
    for length in range(1, history + 1):
        for word in itertools.product(range(length), repeat=length):
            if word[0] != 0 or any(value > max(word[:index]) + 1 for index, value in enumerate(word[1:], 1)):
                continue
            values.add("".join(str(value) for value in word))
    return tuple(sorted(values, key=lambda value: (len(value), value)))


class PatternHead:
    def __init__(self, history=6, hidden_size=8, seed=5401):
        self.history = history; self.vocabulary = pattern_vocabulary(history); self.labels = ()
        self.hidden_size = hidden_size; self.network = None; self.seed = seed; self.input_size = len(self.vocabulary) + 1

    def encode(self, word):
        vector = [0.0] * self.input_size
        vector[self.vocabulary.index(canonical_pattern(word, self.history))] = 1.0
        vector[-1] = min(len(word), self.history) / self.history
        return vector

    def fit(self, observations, epochs=8, learning_rate=0.08):
        self.labels = tuple(sorted({output for _, output in observations}))
        self.network = MLP(self.input_size, self.hidden_size, len(self.labels), self.seed)
        return self.network.train([self.encode(word) for word, _ in observations], [self.labels.index(output) for _, output in observations], epochs, learning_rate)

    def predict(self, word):
        probabilities = self.network.probabilities(self.encode(word)); index = max(range(len(probabilities)), key=probabilities.__getitem__)
        return {"label": self.labels[index], "confidence": probabilities[index]}

    def challenge_score(self, word):
        return 1.0 - self.predict(word)["confidence"]
