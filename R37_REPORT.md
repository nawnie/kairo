# Kairo R37: path-only question session

## Delivered boundary

The caller supplies one program path. The program implements the existing
opaque reset/step adapter boundary (`describe`, `reset`, `step`). Kairo learns
the finite observable behavior once, then accepts multiple natural-language
questions in one session.

For each question Kairo:

1. extracts an explicit or uniquely inferable bounded action plan;
2. runs the learned model on that plan;
3. executes the same plan against a fresh program process;
4. returns an answer only when prediction and fresh trace agree;
5. returns `abstain` otherwise.

Boolean-like observations can be rendered as yes/no predicates. Bounded
quantifiers (`once`, `twice`, `thrice`, and `N times` through eight) are
supported. The raw action/output trace remains attached to every answer.

## User entry point

```text
py -3.12 -m kairo_r24.ask --interactive PROGRAM_PATH
```

Input is one question per line; output is one JSON result per line. An
embedding caller can use `Questioner` to keep the model in memory across
questions.

## Verification

- R24 path/question/session tests: 11/11 passed.
- Preserved R23 regression tests: 12/12 passed.
- `path_program.py`, `path_learn.py`, `question_path.py`, and `ask.py`
  compile successfully.

## Scope limits

This is not unrestricted natural-language understanding. Semantic planning is
currently limited to explicit action names, a small intent vocabulary, unique
change/observation compositions, and bounded repetition. Programs outside the
adapter boundary are not silently interpreted, and ambiguous questions
abstain. The next experiment should broaden semantic planning while retaining
fresh-trace verification and the existing learner/evaluator separation.
