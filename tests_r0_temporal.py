import unittest

from kairo_r0.temporal import TemporalReadout, run_case


class R0TemporalTests(unittest.TestCase):
    def test_readout_round_trip(self):
        model = TemporalReadout(3, nonlinear=True).fit([0, 1, 0, 1, 1, 0])
        restored = TemporalReadout.from_json(model.to_json())
        self.assertEqual(model.predict([0, 1, 0]), restored.predict([0, 1, 0]))

    def test_all_frozen_regimes_emit_receipts(self):
        for kind in ("delayed", "parity", "reversal"):
            row = run_case(kind, 17)
            self.assertEqual(row["r0_ngrc_mae"], row["reload_mae"])
            self.assertGreaterEqual(row["base_mae"], 0.0)


if __name__ == "__main__":
    unittest.main()
