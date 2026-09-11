# R53-N0 supervised-training contract

N0 training now has an explicit teacher boundary in
`kairo_n0/contract.py`. A verified observation carries task family, episode,
prefix, output, and verification receipt ID. Only prefix/output pairs are
exported to the neural helper. Evaluator models, expected artifacts, hidden
state, exactness, goal status, private cases, and post-hoc correctness are
rejected or omitted.

The next N0 promotion run must use disjoint task families for training and
held-out evaluation, matched symbolic/random/N-ranked policies, a 512-example
and eight-epoch ceiling, resource telemetry, and independent artifact/product
model/replay checks. The current R51-N0 result remains non-promoted because
ranking instability fails that gate.
