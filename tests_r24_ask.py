import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class AskCliTests(unittest.TestCase):
    def test_interactive_cli_uses_only_one_supplied_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("This tool converts records to JSON.\n", encoding="utf-8")
            (root / "main.py").write_text(
                "def save():\n    pass\n\ndef run():\n    return save()\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-m", "kairo_r24.ask", "--interactive", str(root)],
                input="what does this program do?\nhow does run reach save?\n",
                text=True,
                capture_output=True,
                cwd=Path(__file__).parent,
                check=True,
            )
            answers = [json.loads(line) for line in completed.stdout.splitlines()]
            self.assertEqual(len(answers), 2)
            self.assertEqual(answers[0]["status"], "answered")
            self.assertIn("converts records to JSON", answers[0]["answer"])
            self.assertEqual(answers[1]["answer"], "run -> save")


if __name__ == "__main__":
    unittest.main()
