import tempfile
import unittest
from pathlib import Path

from kairo_r24.source_path import summarize_path
from kairo_r24.question_path import Questioner


class SourcePathTests(unittest.TestCase):
    def test_program_summary_uses_readme_and_python_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("# Demo\nThis program answers inventory questions.\n", encoding="utf-8")
            (root / "main.py").write_text('"""Runs inventory lookup."""\nimport json\n\ndef lookup():\n    return json.loads("{}")\n', encoding="utf-8")
            result = summarize_path(root)
            self.assertEqual(result["status"], "answered")
            self.assertIn("inventory questions", result["answer"])
            self.assertTrue(any(item["path"].endswith("README.md") for item in result["evidence"]))

    def test_questioner_answers_program_purpose_from_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("This tool converts CSV files to JSON.", encoding="utf-8")
            (root / "tool.py").write_text("def convert():\n    pass\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("what does this program do?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("CSV files", result["answer"])

    def test_questioner_answers_function_purpose_from_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tool.py").write_text('def convert():\n    """Converts CSV rows to JSON."""\n    return encode()\n', encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("what does the function convert do?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("Converts CSV rows to JSON", result["answer"])
            self.assertIn("encode", result["answer"])

    def test_questioner_locates_symbol_from_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "tool.py"
            source.write_text("class Converter:\n    pass\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("where is the class Converter defined?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("tool.py:1", result["answer"])

    def test_questioner_finds_text_evidence_from_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "tool.py"
            source.write_text("inventory = []\nvalue = 'inventory'\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("which files mention inventory?")
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["matches"], 2)
            self.assertTrue(all(item["path"].endswith("tool.py") for item in result["evidence"]))

    def test_program_summary_includes_metadata_and_entrypoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "pyproject.toml").write_text('[project]\nname = "demo-tool"\ndescription = "Processes reports."\n[project.scripts]\ndemo = "main:run"\n', encoding="utf-8")
            (root / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
            result = summarize_path(root)
            self.assertIn("demo-tool", result["answer"])
            self.assertIn("Processes reports", result["answer"])
            self.assertIn("main.py", result["answer"])


if __name__ == "__main__":
    unittest.main()
