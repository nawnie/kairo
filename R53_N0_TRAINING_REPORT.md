# R53-N0 supervised training result

Date: 2026-09-11

The new teacher/learner contract was exercised with eight verified donor
observations and four held-out-family observations. The neural helper had 9
input features, 8 hidden units, 2 output labels, an eight-epoch budget, and a
512-example ceiling. Training took 0.0017 seconds in the local run and the
loss decreased from 0.73946 to 0.69581.

Held-out accuracy was 0/4. This is a valid negative result: the head trained,
but the current raw action/history representation did not transfer to the
held-out family. N0 remains unpromoted. Increasing network size is not yet
justified; the next experiment should test a structured binding-invariant
representation and a matched simpler control.

Receipt: `verification/R53_N0_TRAINING.json`.
