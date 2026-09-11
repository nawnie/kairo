# R49: open-world drift refusal

Date: 2026-09-11

The focused test `tests_r49_openworld.py` passed. It constructs a drifting
adapter whose repeated prefix changes output and verifies that the learner
raises a `ValueError` containing `non-determinism` instead of smoothing the
contradiction into a model.

This is a unit-level refusal result. It is not evidence of broad open-world
robustness, autonomous drift handling, or general intelligence.
