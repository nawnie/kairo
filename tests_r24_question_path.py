import json
import tempfile
import unittest
from pathlib import Path

from kairo_r24.question_path import ask_path, Questioner


ADAPTER = '''
import json
import sys
state = 0
for line in sys.stdin:
    request = json.loads(line)
    if request["op"] == "describe": response = {"alphabet": ["flip", "read"]}
    elif request["op"] == "reset": state = 0; response = {"ok": True}
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


class QuestionPathTests(unittest.TestCase):
    def test_question_returns_observed_answer_and_trace(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = ask_path(path, "what happens after flip then read?", PROTOCOL)
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["answer"], "on")
            self.assertEqual([x["action"] for x in result["trace"]], ["flip", "read"])

    def test_unknown_question_abstains(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = ask_path(path, "why is the system correct?", PROTOCOL)
            self.assertEqual(result["status"], "abstain")

    def test_semantic_status_question_uses_read_action(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = ask_path(path, "what is the current status?", PROTOCOL)
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["plan"], ["read"])
            self.assertEqual(result["answer"], "no")

    def test_semantic_multi_step_change_then_status(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = ask_path(path, "what is the status after toggling?", PROTOCOL)
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["plan"], ["flip", "read"])
            self.assertEqual(result["answer"], "yes")

    def test_boolean_question_returns_predicate_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = ask_path(path, "will it be on after toggling?", PROTOCOL)
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["answer"], "yes")
            self.assertEqual(result["trace"][-1]["output"], "on")

    def test_quantified_multi_step_question(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            result = ask_path(path, "what is the status after toggling twice?", PROTOCOL)
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["plan"], ["flip", "flip", "read"])
            self.assertEqual(result["answer"], "no")

    def test_questioner_reuses_learned_model(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            questioner = Questioner(path, PROTOCOL)
            first = questioner.ask("what is the current status?")
            second = questioner.ask("will it be on after toggling?")
            self.assertEqual(first["status"], "answered")
            self.assertEqual(second["status"], "answered")
            self.assertEqual(first["learning"]["queries"], second["learning"]["queries"])

    def test_session_handles_multiple_questions_from_one_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            questioner = Questioner(path, PROTOCOL)
            answers = [questioner.ask(question) for question in (
                "what is the current status?",
                "will it be on after toggling?",
                "what is the status after toggling twice?",
            )]
            self.assertEqual([item["status"] for item in answers], ["answered"] * 3)
            self.assertEqual([item["answer"] for item in answers], ["no", "yes", "no"])

    def test_relational_question_compares_with_original_state(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            questioner = Questioner(path, PROTOCOL)
            result = questioner.ask("does toggling twice return to the original status?")
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["plan"], ["flip", "flip", "read"])
            self.assertEqual(result["answer"], "yes")

    def test_change_question_returns_transition(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            questioner = Questioner(path, PROTOCOL)
            result = questioner.ask("what changes after toggling?")
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["plan"], ["flip", "read"])
            self.assertEqual(result["answer"], "off -> on")

    def test_model_level_question_needs_no_action_name(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.py"
            path.write_text(ADAPTER, encoding="utf-8")
            questioner = Questioner(path, PROTOCOL)
            result = questioner.ask("how many states does this program have?")
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["answer"], "2")
            self.assertEqual(result["evidence"]["kind"], "learned_model")


if __name__ == "__main__":
    unittest.main()
