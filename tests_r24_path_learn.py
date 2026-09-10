import json
import tempfile
import unittest
from pathlib import Path

from kairo_r24.path_learn import learn_path


ADAPTER = '''
import json
import sys
state = 0
for line in sys.stdin:
    request = json.loads(line)
    if request["op"] == "describe":
        response = {"alphabet": ["flip", "read"]}
    elif request["op"] == "reset":
        state = 0
        response = {"ok": True}
    elif request["op"] == "step":
        if request["action"] == "flip": state = 1 - state
        response = {"output": "on" if state else "off"}
    print(json.dumps(response), flush=True)
'''


PROTOCOL = {
    "initial_suffix_depth": 1, "query_budget": 200, "symbol_budget": 1000,
    "seed": 7, "middle_depth": 2, "max_middle_depth": 2,
    "random_probes": 20, "random_max_length": 4, "round_budget": 8,
}


class PathLearningTests(unittest.TestCase):
    def test_existing_learner_can_learn_supplied_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = learn_path(path, PROTOCOL)
            self.assertEqual(result["status"], "provisional_no_counterexample_in_bounded_probes")
            self.assertEqual(result["alphabet"], ["flip", "read"])
            self.assertIsNotNone(result["model"])
            self.assertGreater(result["queries"], 0)


if __name__ == "__main__":
    unittest.main()
