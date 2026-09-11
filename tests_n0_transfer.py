import unittest

from kairo_n0.transfer import TARGET, run


class N0TransferTests(unittest.TestCase):
    def test_target_is_external_to_training(self):
        result = run()
        self.assertEqual(result.hidden_target, TARGET)
        self.assertGreater(result.candidate_count, 1)

    def test_neural_ranking_is_deterministic(self):
        first = run(seed=5101)
        second = run(seed=5101)
        self.assertEqual(first.neural_rank, second.neural_rank)
        self.assertEqual(first.random_ranks, second.random_ranks)


if __name__ == "__main__":
    unittest.main()
