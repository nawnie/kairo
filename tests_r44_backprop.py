import unittest

from kairo_r44.backprop import MLP, TraceHead


class BackpropTests(unittest.TestCase):
    def test_gradient_training_reduces_loss(self):
        network = MLP(2, 5, 2, seed=44)
        losses = network.train([[1.0, 0.0], [0.0, 1.0]], [0, 1], epochs=2000, learning_rate=0.12)
        self.assertLess(losses[-1], losses[0])
        self.assertGreater(network.probabilities([1.0, 0.0])[0], 0.7)
        self.assertGreater(network.probabilities([0.0, 1.0])[1], 0.7)

    def test_trace_head_uses_observed_labels_only(self):
        head = TraceHead(["open", "close"], seed=44)
        self.assertIsNone(head.predict(["open"]))
        head.fit([([], "session_opened"), (["open"], "session_closed")], epochs=100)
        self.assertEqual(set(head.labels), {"session_opened", "session_closed"})
        self.assertIn(head.predict(["open"])["label"], head.labels)

    def test_repeated_initialization_is_deterministic(self):
        data = [([], "a"), (["open"], "b"), (["close"], "a")]
        first = TraceHead(["open", "close"], seed=99); second = TraceHead(["open", "close"], seed=99)
        first.fit(data, epochs=20); second.fit(data, epochs=20)
        self.assertEqual(first.predict(["open"]), second.predict(["open"]))


if __name__ == "__main__": unittest.main()
