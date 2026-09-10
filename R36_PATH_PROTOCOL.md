# R36: supplied program-path boundary

R36 extends the existing R24 learner boundary to a user-supplied program
path. The child program is launched directly and speaks newline-delimited JSON:

- `describe` returns a non-empty string action alphabet.
- `reset` returns `{ "ok": true }` and must clear the child state.
- `step` accepts one alphabet action and returns one string observation.

Only these observations cross the boundary. The learner does not receive the
child's source, private state, evaluator truth, or filesystem contents. The
next step is to connect this boundary to the existing observation-table
learner and then add question-to-plan behavior with explicit abstention.
