import unittest

from kairo_n0.n1_experiment import run


class N1ExperimentTests(unittest.TestCase):
    def test_binding_invariant_representation_transfers(self):
        result = run()
        self.assertGreater(result["structured_accuracy"], result["raw_accuracy"])
        self.assertGreater(result["structured_accuracy"], result["random_accuracy_mean"])
        self.assertFalse(result["evaluator_truth_in_training"])
        self.assertFalse(result["kairo_promotion"])


if __name__ == "__main__":
    unittest.main()
