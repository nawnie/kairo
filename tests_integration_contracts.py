import unittest

from kairo_interfaces.contracts import CanonicalResult, DynamicContext, NeuralProposal, apply_context


class IntegrationContractTests(unittest.TestCase):
    def setUp(self):
        self.result = CanonicalResult({"ok": True}, "fresh_verified", "symbolic_external")
        self.context = DynamicContext("r0", (0.2, 0.8), 1.0, "r0-test", ("e1", "e2"))

    def test_context_cannot_change_canonical_result(self):
        application = apply_context(self.context, self.result, NeuralProposal(("op_1",), 0.7))
        self.assertEqual(application.canonical_before, application.canonical_after)
        self.assertFalse(application.authority_changed)

    def test_provenance_and_weights_are_bounded(self):
        with self.assertRaises(ValueError):
            DynamicContext("r0", (0.1,), 1.1, "hash", ("e1",))
        with self.assertRaises(ValueError):
            DynamicContext("r0", (0.1,), 0.5, "", ("e1",))

    def test_unlocked_result_is_rejected(self):
        with self.assertRaises(ValueError):
            CanonicalResult({}, "unknown", "none", locked=False)


if __name__ == "__main__": unittest.main()
