import unittest

from kairo_r62_offline.experiment import run


class R62OfflineTests(unittest.TestCase):
    def test_replay_covers_frozen_cases(self):
        result = run()
        self.assertEqual(len(result["rows"]), 9)
        self.assertTrue(all(row["candidate_count"] == 8 for row in result["rows"]))


if __name__ == "__main__": unittest.main()
