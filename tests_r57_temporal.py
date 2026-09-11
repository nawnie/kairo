import unittest

from kairo_r57.experiment import run


class R57TemporalTests(unittest.TestCase):
    def test_broader_receipt_has_five_by_five_cases(self):
        result = run()
        self.assertEqual(result["case_count"], 25)
        self.assertTrue(result["reload_exact"])
        self.assertGreater(result["r0_wins_fixed"], 0)


if __name__ == "__main__":
    unittest.main()
