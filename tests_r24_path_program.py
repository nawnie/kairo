import json
import tempfile
import unittest
from pathlib import Path

from kairo_r24.path_program import PathProgram


ADAPTER = '''
import json
import sys
state = 0
for line in sys.stdin:
    request = json.loads(line)
    if request["op"] == "describe":
        response = {"alphabet": ["a", "b"]}
    elif request["op"] == "reset":
        state = 0
        response = {"ok": True}
    elif request["op"] == "step":
        state += 1
        response = {"output": f"{request['action']}:{state}"}
    else:
        response = {"error": "unknown operation"}
    print(json.dumps(response), flush=True)
'''


class PathProgramTests(unittest.TestCase):
    def test_path_boundary_describe_reset_step(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            with PathProgram(path) as program:
                self.assertEqual(program.describe(), ("a", "b"))
                program.reset()
                self.assertEqual(program.step("a"), "a:1")
                self.assertEqual(program.step("b"), "b:2")

    def test_missing_path_is_rejected(self):
        with self.assertRaises(Exception):
            PathProgram("missing-program.py")


if __name__ == "__main__":
    unittest.main()
