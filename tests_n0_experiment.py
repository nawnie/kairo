import unittest

from kairo_n0.experiment import run


class N0ExperimentTests(unittest.TestCase):
    def test_supervised_receipt_is_proposal_only(self):
        result = run()
        self.assertTrue(result["proposal_only"])
        self.assertFalse(result["evaluator_fields_in_learner"])
        self.assertEqual(result["train_count"], 8)
        self.assertEqual(result["heldout_total"], 4)
        self.assertEqual(result["network"]["hidden_units"], 8)


if __name__ == "__main__":
    unittest.main()
