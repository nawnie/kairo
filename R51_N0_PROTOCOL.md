# R51-N0: bounded transfer probe

N0 receives only donor `(action-prefix, returned-output)` observations. It
trains the existing tiny deterministic head and ranks fresh challenge words
by uncertainty. The target mismatch is frozen outside the learner. A random
control receives the same candidate pool and budget. No expected artifact,
hidden state, evaluator label, or target identity is given to N0 during
training.

This is an isolated proposal-ranking capability test, not a correctness test.
The required next Kairo gate is the same design on fresh changed-binding and
hidden-state program cases with symbolic, random, and N-ranked policies.
