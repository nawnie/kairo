import copy
import json
import tempfile
import unittest
from pathlib import Path

from kairo_r43.audit import exact_model, product, replay
from kairo_r43.backend import FileWorkflow
from kairo_r11.model import Model


class R43AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads(Path("datasets/r43/private_cases.json").read_text())[0]

    def test_independent_product_has_expected_depth(self):
        target, states = product(self.case)
        self.assertEqual(states, 11)
        self.assertEqual(len(target["transitions"]), 11)

    def test_model_fault_is_rejected(self):
        target, _ = product(self.case)
        with tempfile.TemporaryDirectory() as directory:
            backend = FileWorkflow(Path(directory) / "x", self.case)
            from kairo_r24.backend import explore
            model = explore(backend, 64)["model"]
        broken = {"schema": "kairo.symbolic-mealy.v1", "alphabet": model["alphabet"], "transitions": []}
        for index in range(len(model["transitions"])):
            row = []
            for action in model["alphabet"]:
                next_state, output = model["transitions"]["s" + str(index)][action]
                row.append([int(next_state[1:]), output])
            broken["transitions"].append(row)
        broken["transitions"][0][0][1] = "fabricated_output"
        self.assertFalse(exact_model(broken, target))

    def test_replay_fault_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FileWorkflow(Path(directory) / "x", self.case)
            actual = backend.step("op_0")
        events = [{"request": {"op": "step", "action": "op_0"}, "response": {"output": "fabricated_output"}}]
        self.assertNotEqual(actual, events[0]["response"]["output"])


if __name__ == "__main__":
    unittest.main()
