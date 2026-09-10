"""Small deterministic backpropagation head for observed trace exploration.

This is deliberately auxiliary: it learns only labels returned by the
observed system. It cannot certify a model, access evaluator-only state, or
replace the symbolic conformance/replay gate.
"""
import math


def _sigmoid(value):
    value = max(-40.0, min(40.0, value))
    return 1.0 / (1.0 + math.exp(-value))


class MLP:
    def __init__(self, input_size, hidden_size, output_size, seed=4401):
        if min(input_size, hidden_size, output_size) <= 0:
            raise ValueError("layer sizes must be positive")
        self.input_size = input_size; self.hidden_size = hidden_size; self.output_size = output_size
        state = seed & 0xFFFFFFFF
        def next_weight():
            nonlocal state
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            return ((state / 0xFFFFFFFF) * 2.0 - 1.0) * 0.15
        self.w1 = [[next_weight() for _ in range(input_size)] for _ in range(hidden_size)]
        self.b1 = [0.0] * hidden_size
        self.w2 = [[next_weight() for _ in range(hidden_size)] for _ in range(output_size)]
        self.b2 = [0.0] * output_size

    def _forward(self, values):
        if len(values) != self.input_size: raise ValueError("input width mismatch")
        hidden = [math.tanh(sum(weight * value for weight, value in zip(row, values)) + bias) for row, bias in zip(self.w1, self.b1)]
        logits = [sum(weight * value for weight, value in zip(row, hidden)) + bias for row, bias in zip(self.w2, self.b2)]
        scale = max(logits); exponentials = [math.exp(value - scale) for value in logits]; total = sum(exponentials)
        return hidden, [value / total for value in exponentials]

    def probabilities(self, values):
        return self._forward(values)[1]

    def train(self, samples, labels, epochs=80, learning_rate=0.08):
        if not samples or len(samples) != len(labels): raise ValueError("training data mismatch")
        if any(label < 0 or label >= self.output_size for label in labels): raise ValueError("label outside output layer")
        losses = []
        for _ in range(epochs):
            loss = 0.0
            for values, label in zip(samples, labels):
                hidden, probabilities = self._forward(values)
                loss -= math.log(max(probabilities[label], 1e-12))
                delta2 = list(probabilities); delta2[label] -= 1.0
                delta1 = [hidden_index * (1.0 - hidden_index * hidden_index) * sum(delta2[out] * self.w2[out][hidden_index] for out in range(self.output_size)) for hidden_index in range(self.hidden_size)]
                for out in range(self.output_size):
                    for hidden_index in range(self.hidden_size): self.w2[out][hidden_index] -= learning_rate * delta2[out] * hidden[hidden_index]
                    self.b2[out] -= learning_rate * delta2[out]
                for hidden_index in range(self.hidden_size):
                    for input_index in range(self.input_size): self.w1[hidden_index][input_index] -= learning_rate * delta1[hidden_index] * values[input_index]
                    self.b1[hidden_index] -= learning_rate * delta1[hidden_index]
            losses.append(loss / len(samples))
        return losses


class TraceHead:
    """Backprop-trained next-output predictor over observed trace prefixes."""
    def __init__(self, alphabet, history=6, hidden_size=12, seed=4401):
        self.alphabet = tuple(alphabet); self.history = history; self.labels = (); self.network = None; self.seed = seed
        self.input_size = len(self.alphabet) * history + 1

    def encode(self, word):
        vector = [0.0] * self.input_size
        for offset, action in enumerate(list(word)[-self.history:]):
            if action not in self.alphabet: raise ValueError("unknown action")
            vector[offset * len(self.alphabet) + self.alphabet.index(action)] = 1.0
        vector[-1] = min(len(word), self.history) / self.history
        return vector

    def fit(self, observations, epochs=80, learning_rate=0.08):
        if not observations: raise ValueError("observations required")
        self.labels = tuple(sorted({output for _, output in observations}))
        self.network = MLP(self.input_size, max(2, min(32, 2 * len(self.alphabet))), len(self.labels), self.seed)
        samples = [self.encode(word) for word, _ in observations]
        indices = [self.labels.index(output) for _, output in observations]
        return self.network.train(samples, indices, epochs, learning_rate)

    def predict(self, word):
        if self.network is None: return None
        probabilities = self.network.probabilities(self.encode(word)); index = max(range(len(probabilities)), key=probabilities.__getitem__)
        return {"label": self.labels[index], "confidence": probabilities[index], "uncertainty": 1.0 - probabilities[index], "probabilities": dict(zip(self.labels, probabilities))}

    def challenge_score(self, word):
        prediction = self.predict(word)
        return prediction["uncertainty"] if prediction else 1.0
