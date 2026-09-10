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

    def test_questioner_answers_function_relationships(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tool.py").write_text("def helper():\n    pass\n\ndef run():\n    return helper()\n", encoding="utf-8")
            questioner = Questioner(root, {})
            calls = questioner.ask("what does the function run call?")
            callers = questioner.ask("who calls the function helper?")
            self.assertIn("helper", calls["answer"])
            self.assertIn("run", callers["answer"])

    def test_questioner_answers_bounded_call_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tool.py").write_text("def save():\n    pass\n\ndef convert():\n    return save()\n\ndef run():\n    return convert()\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("how does the function run reach the function save?")
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["answer"], "run -> convert -> save")

    def test_questioner_answers_function_parameters(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tool.py").write_text("def convert(source, destination='out.json'):\n    return source\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("what inputs does the function convert accept?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("source, destination", result["answer"])

    def test_function_summary_reports_side_effect_operations(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tool.py").write_text("def save(path):\n    return open(path, 'w')\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("what does the function save do?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("Source-visible operations: open", result["answer"])

    def test_program_summary_includes_metadata_and_entrypoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "pyproject.toml").write_text('[project]\nname = "demo-tool"\ndescription = "Processes reports."\n[project.scripts]\ndemo = "main:run"\n', encoding="utf-8")
            (root / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
            result = summarize_path(root)
            self.assertIn("demo-tool", result["answer"])
            self.assertIn("Processes reports", result["answer"])
            self.assertIn("main.py", result["answer"])

    def test_program_summary_reports_code_operations(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "main.py").write_text("def run():\n    with open('input.txt') as stream:\n        return stream.read()\n\nif __name__ == '__main__':\n    run()\n", encoding="utf-8")
            result = summarize_path(root)
            self.assertIn("open", result["answer"])
            self.assertIn("__main__", " ".join(item["text"] for item in result["evidence"]))

    def test_questioner_answers_source_capability(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "main.py").write_text("import socket\n\ndef run():\n    return socket.socket()\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("does this program use the network?")
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["answer"], "yes")
            self.assertGreater(result["matches"], 0)

    def test_questioner_answers_dependencies_and_entrypoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "main.py").write_text("import sqlite3\n\ndef run():\n    return sqlite3.connect(':memory:')\n", encoding="utf-8")
            questioner = Questioner(root, {})
            dependencies_result = questioner.ask("what are the dependencies?")
            entrypoint_result = questioner.ask("what is the entry point?")
            self.assertIn("sqlite3", dependencies_result["answer"])
            self.assertIn("main.py", entrypoint_result["answer"])

    def test_open_ended_source_question_returns_ranked_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "auth.py").write_text("def authenticate(token):\n    return validate_token(token)\n", encoding="utf-8")
            questioner = Questioner(root, {})
            result = questioner.ask("how does authentication work?")
            self.assertEqual(result["status"], "answered")
            self.assertIn("authentication", result["answer"])
            self.assertTrue(any("authenticate" in item["text"] for item in result["evidence"]))

    def test_program_summary_reads_mixed_language_structure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "index.ts").write_text("import express from 'express';\nexport function startServer() { return express(); }\n", encoding="utf-8")
            result = summarize_path(root)
            evidence = " ".join(item["text"] for item in result["evidence"])
            self.assertIn("express", evidence)
            self.assertIn("startServer", evidence)


if __name__ == "__main__":
    unittest.main()
