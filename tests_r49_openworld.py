import unittest

from kairo_r11.learn import Learner
from kairo_r49.drift import DriftingAdapter


class OpenWorldRefusalTests(unittest.TestCase):
    def test_contradictory_prefix_is_rejected(self):
        adapter = DriftingAdapter()
        protocol = {"seed": 49, "query_budget": 20, "symbol_budget": 100, "initial_suffix_depth": 1}
        learner = Learner(["op_0"], lambda word: (adapter.reset(), [adapter.step(action) for action in word])[1], protocol)
        learner.ask(("op_0",))
        with self.assertRaises(ValueError) as failure:
            learner.ask(("op_0", "op_0"))
        self.assertIn("non-determinism", str(failure.exception))


if __name__ == "__main__": unittest.main()
