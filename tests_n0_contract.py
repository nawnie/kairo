import unittest

from kairo_n0.contract import VerifiedObservation, freeze_split, reject_privileged_payload, teacher_export


class N0ContractTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            VerifiedObservation("donor", "d1", ("a",), "zero", "v1"),
            VerifiedObservation("donor", "d2", ("b",), "one", "v2"),
            VerifiedObservation("heldout", "h1", ("c",), "zero", "v3"),
        ]

    def test_family_split_is_disjoint(self):
        train, heldout = freeze_split(self.rows, {"heldout"})
        self.assertEqual({row.episode_id for row in train}, {"d1", "d2"})
        self.assertEqual({row.episode_id for row in heldout}, {"h1"})

    def test_export_strips_verification_metadata(self):
        self.assertEqual(teacher_export(self.rows)[0], {"prefix": ["a"], "output": "zero"})

    def test_privileged_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            reject_privileged_payload({"output": "zero", "exactness": True})


if __name__ == "__main__":
    unittest.main()
