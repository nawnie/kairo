import unittest

from kairo_r60_weight.experiment import run


class R60WeightTests(unittest.TestCase):
    def test_weight_sweep_is_complete(self):
        result = run()
        self.assertEqual(result["case_count"], 125)
        self.assertIn(result["best_weight"], (0.0, 0.25, 0.5, 0.75, 1.0))


if __name__ == "__main__": unittest.main()
