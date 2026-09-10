# R37: question over a supplied program path

The caller supplies only a program path and a natural-language question. The
program declares its opaque action alphabet through `describe`; Kairo extracts
an action plan from explicit action names or a unique intent match (for
example, “current status” can select a unique `read` action, while “status
after toggling” can compose unique `flip` and `read` actions). It
learns the program through the existing reset/step observation-table boundary,
executes the planned actions independently, and answers only when the learned
prediction matches the fresh trace. The answer includes the action/output
trace as evidence. Boolean-like observations (`on`/`off`, `true`/`false`, or
`yes`/`no`) can also be rendered as a yes/no answer when the question is
predicate-shaped.
Simple bounded quantifiers (`once`, `twice`, `thrice`, or `N times` for
`1 <= N <= 8`) can repeat the uniquely identified state-changing action before
the observation action.
Relational predicate questions can compare a post-plan observation with a
fresh baseline observation, such as whether repeated toggling returns to the
original state.
Questions containing “what changes” can return a baseline-to-post-plan
transition such as `off -> on`.
Model-level questions such as “how many states does this program have?” and
“how many actions does it expose?” do not require action names; their answers
come from the learned model and declared alphabet respectively.

Questions without an unambiguous action plan, incomplete learning, or a model
trace mismatch abstain. This is the first usable interaction checkpoint, not
general natural-language understanding; the next work is semantic planning
and held-out questions without action names while preserving the same evidence
and abstention rules.

User entry point:

`py -3.12 -m kairo_r24.ask PROGRAM_PATH "question containing the action sequence"`

For a path-only interactive session:

`py -3.12 -m kairo_r24.ask --interactive PROGRAM_PATH`

Then provide one question per input line. Each line returns one JSON answer.

Embedding callers can create one `Questioner` for a program path and submit
multiple questions; the learned model is reused while each answer still gets a
fresh independent trace check.
