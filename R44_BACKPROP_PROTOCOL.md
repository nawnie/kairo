# R44 backpropagation auxiliary protocol

Backpropagation is added as an ablation, not as a replacement for Kairo's
symbolic conformance learner.

The neural head may consume only observed `(action-prefix, returned-output)`
pairs from the probe boundary. It may predict output labels, uncertainty, and
which fresh challenge to query. It may not receive private cases, evaluator
models, expected artifacts, hidden state IDs, or post hoc exactness labels.

The first comparison must include:

- symbolic learner alone;
- backprop head used only to rank fresh challenges;
- matched random challenge control;
- matched compute/query/resource budgets.

The auxiliary observation buffer is bounded at 512 prefix/output examples
per task using deterministic reservoir replacement, and the first ablation
uses eight local training epochs. The head's parameter
count depends only on the action alphabet, history window, and observed output
labels; it is not allowed to grow with the entire project or indefinitely with
runtime.

The symbolic model, artifact check, independent product traversal, and replay
remain the acceptance gates. A lower loss, higher confidence, or faster
challenge ranking is not model correctness. Any claimed benefit must survive
fresh cases, changed action bindings, negative fault injection, and the safety
gate before broader program tests.
