# R58-R1 protocol

R1 is the actual recurrent reservoir lane, not the R0 nonlinear-VAR lane.
The frozen comparison uses constant-history, fixed-window, and one seeded
sparse leaky reservoir configuration across delayed, parity, reversal, and
unseen-delay temporal families. Training uses washout and ridge readout only;
the reservoir state is context, never evidence or symbolic acceptance.

Promotion requires no correctness/replay regression, exact reload, resource
receipts, and a reproducible advantage over the simpler fixed-window control.
