"""Minimal question-to-plan interface over a learned program path.

This is intentionally conservative: action names must occur in the supplied
question. It never invents an action or claims an answer when planning is
ambiguous.
"""
from __future__ import annotations

import re
from pathlib import Path

from .path_learn import learn_path
from .path_program import PathProgram
from kairo_r11.model import Model
from .source_path import capability, find_symbol, find_text, summarize_function, summarize_path


def _plan(question, alphabet):
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_-]*", question.lower())
    normalized = {action.lower(): action for action in alphabet}
    explicit = [normalized[word] for word in words if word in normalized]
    if explicit:
        return explicit
    intent_groups = (
        {"status", "state", "value", "current", "now", "read", "show", "see", "what"},
        {"flip", "toggle", "toggling", "switch", "change", "changes", "changing"},
        {"begin", "start", "open"},
        {"finish", "commit", "save", "write"},
        {"undo", "rollback", "reset", "restore"},
    )
    question_words = set(words)
    candidates = []
    for action in alphabet:
        action_words = set(re.findall(r"[a-zA-Z]+", action.lower()))
        score = max((len(action_words & group) for group in intent_groups if question_words & group), default=0)
        if score:
            candidates.append((score, action))
    if not candidates:
        return []
    # Compose a state-changing intent with a unique observation intent when
    # the question explicitly asks for the result after the change.
    if {"after", "following", "then", "return", "original"} & question_words:
        change_words = {"flip", "toggle", "toggling", "switch", "switching", "change", "changing", "begin", "start", "open", "finish", "commit", "save", "write", "undo", "rollback", "reset", "restore"}
        observe_words = {"status", "state", "value", "current", "read", "show", "see", "what", "on", "off", "true", "false"}
        change = [action for action in alphabet if set(re.findall(r"[a-zA-Z]+", action.lower())) & change_words]
        observe = [action for action in alphabet if set(re.findall(r"[a-zA-Z]+", action.lower())) & observe_words]
        if len(change) == 1 and len(observe) == 1 and change[0] != observe[0] and (question_words & change_words) and (question_words & observe_words):
            count = 1
            number_words = {"once": 1, "twice": 2, "thrice": 3}
            for word, value in number_words.items():
                if word in question_words:
                    count = value
            numeric = re.search(r"\b(\d+)\s+times?\b", question.lower())
            if numeric:
                count = int(numeric.group(1))
            if 1 <= count <= 8:
                return [change[0]] * count + [observe[0]]
    best = max(score for score, _ in candidates)
    winners = [action for score, action in candidates if score == best]
    return [winners[0]] if len(winners) == 1 else []


class Questioner:
    def __init__(self, program_path, protocol):
        self.program_path = str(program_path)
        self.protocol = protocol
        if Path(program_path).expanduser().resolve().is_dir():
            self.alphabet = ()
            self.learning = {"status": "source_only", "queries": 0, "model": None}
        else:
            with PathProgram(program_path) as program:
                self.alphabet = program.describe()
            self.learning = learn_path(program_path, protocol)

    def ask(self, question):
        function_match = re.search(r"\bwhat does (?:the )?function\s+([A-Za-z_]\w*)\s+do\b", question, re.IGNORECASE)
        if function_match:
            return summarize_function(self.program_path, function_match.group(1))
        symbol_match = re.search(r"\bwhere is (?:the )?(?:function|class)\s+([A-Za-z_]\w*)\s+defined\b", question, re.IGNORECASE) or re.search(r"\bwhere is (?:the )?([A-Za-z_]\w*)\s+defined\b", question, re.IGNORECASE)
        if symbol_match:
            return find_symbol(self.program_path, symbol_match.group(1))
        text_match = re.search(r"\b(?:which files|where) (?:mention|contain)\s+['\"]?([^'\"?]+?)['\"]?\s*\??$", question, re.IGNORECASE)
        if text_match:
            return find_text(self.program_path, text_match.group(1).strip())
        capability_match = re.search(r"\bdoes (?:this )?program use (?:the )?(network|files?|database|processes?)\b", question, re.IGNORECASE)
        if capability_match:
            name = capability_match.group(1).lower().rstrip("s")
            return capability(self.program_path, {"file": "file", "database": "database", "network": "network", "processe": "process"}.get(name, name))
        if re.search(r"\bwhat does (this )?(program|project|code) do\b", question.lower()):
            return summarize_path(self.program_path)
        plan = _plan(question, self.alphabet)
        program_path = self.program_path
        alphabet = self.alphabet
        learned = self.learning
        lowered_question = question.lower()
        if "how many" in lowered_question and "state" in lowered_question and learned.get("model"):
            state_count = len(learned["model"]["transitions"])
            return {"status": "answered", "answer": str(state_count),
                    "program_path": program_path, "plan": [],
                    "evidence": {"kind": "learned_model", "states": state_count},
                    "learning": {"status": learned["status"], "queries": learned["queries"]}}
        if "how many" in lowered_question and ("action" in lowered_question or "operation" in lowered_question):
            return {"status": "answered", "answer": str(len(alphabet)),
                    "program_path": program_path, "plan": [],
                    "evidence": {"kind": "declared_alphabet", "alphabet": list(alphabet)},
                    "learning": {"status": learned["status"], "queries": learned["queries"]}}
        if not plan:
            return {"status": "abstain", "reason": "no_unambiguous_action_plan",
                    "answer": None, "program_path": program_path, "plan": []}
        if not learned.get("model"):
            return {"status": "abstain", "reason": "learning_incomplete",
                    "answer": None, "program_path": program_path, "plan": plan,
                    "learning": learned}
        predicted = list(Model.from_dict(learned["model"]).run(plan))
        trace = []
        with PathProgram(program_path) as program:
            program.describe()
            program.reset()
            for action in plan:
                trace.append({"action": action, "output": program.step(action)})
        if [item["output"] for item in trace] != predicted:
            return {"status": "abstain", "reason": "model_trace_mismatch",
                    "answer": None, "program_path": program_path, "plan": plan,
                    "predicted": predicted, "trace": trace, "learning": learned}
        answer = trace[-1]["output"]
        question_words = set(re.findall(r"[a-zA-Z]+", lowered_question))
        if "change" in question_words or "changes" in question_words:
            with PathProgram(program_path) as baseline_program:
                baseline_program.describe()
                baseline_program.reset()
                baseline = baseline_program.step(plan[-1])
            answer = f"{baseline} -> {answer}"
        elif {"return", "original"} <= question_words:
            with PathProgram(program_path) as baseline_program:
                baseline_program.describe()
                baseline_program.reset()
                baseline = baseline_program.step(plan[-1])
            answer = "yes" if answer == baseline else "no"
        elif re.search(r"\b(will|is|are|does|do)\b", lowered_question) and answer.lower() in {"on", "off", "true", "false", "yes", "no"}:
            answer = "yes" if answer.lower() in {"on", "true", "yes"} else "no"
        return {"status": "answered", "answer": answer,
                "program_path": program_path, "plan": plan, "trace": trace,
                "learning": {"status": learned["status"], "queries": learned["queries"]}}


def ask_path(program_path, question, protocol):
    return Questioner(program_path, protocol).ask(question)
