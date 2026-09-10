import tempfile
import unittest
from pathlib import Path

from kairo_r24.question_path import Questioner


class SourceQuestionTests(unittest.TestCase):
    def test_program_question_is_source_evidenced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("""\nfrom pathlib import Path\n\ndef summarize(path):\n    return Path(path).read_text(encoding='utf-8').strip().upper()\n\ndef main():\n    return summarize('input.txt')\n""")
            (root / "input.txt").write_text("hello\n")
            result = Questioner(root, {}).ask("what does this program do?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("source", result["scope"])
            self.assertTrue(result["evidence"])
            self.assertTrue(any("summarize" in item["text"] for item in result["evidence"]))

    def test_unknown_runtime_claim_abstains_or_labels_static_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "main.py").write_text("import socket\n")
            result = Questioner(root, {}).ask("does this program use the network?")
            self.assertIn(result["status"], {"answered", "abstain"})
            if result["status"] == "answered":
                self.assertIn("scope", result)
                self.assertIn("runtime", result["scope"].lower())


if __name__ == "__main__": unittest.main()
