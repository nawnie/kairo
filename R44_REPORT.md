# Kairo R44: backpropagation challenge-selection ablation

Date: 2026-09-10

R44 added a small backpropagation head around the existing symbolic learner.
It received only observed action-prefix/output pairs and ranked the same
bounded challenge candidates used by the control policies. It did not receive
private cases, evaluator models, expected artifacts, hidden state IDs, or
exactness labels.

## Result

| Policy | Tasks | Successful artifacts | Exact independent models | Queries |
|---|---:|---:|---:|---:|
| plan_challenges | 3 | 3/3 | 3/3 | 7,934 |
| random_challenges | 3 | 3/3 | 3/3 | 7,934 |
| backprop_challenges | 3 | 3/3 | 3/3 | 7,934 |

The independent audit checked nine tasks. Every JSON artifact matched its
expected document, every learned model matched the independently enumerated
11-state product, and every recorded step trace replayed successfully.

## Neural resource boundary

For the eight-action adapter, the head used 49 input features, 16 hidden
units, and 16 observed output labels. The online example reservoir was capped
at 512 examples and the ablation used eight local epochs. On D1 it saw 16,196
prefix/output observations but retained only 512. The loss fell from
2.8117435 to 2.7352014.

## Interpretation

This is a validated neutral result, not a neural win. Backpropagation did not
reduce queries, improve exactness, or change task success against the matched
planning and random controls on this workload. The experiment proves that the
small neural head can be inserted without breaking the symbolic correctness
and safety gates; it does not justify claiming that gradients improve Kairo.

The next useful test is not to make this head larger. It should be evaluated
on fresh hidden-state or changed-binding cases where uncertainty ranking could
matter, with compute costs charged and the same independent audit. Any move
toward real-program or unsupervised operation remains subject to
`SAFETY_GATE.md`.

Detailed receipt: `verification/R44_AUDIT.json`.
