# R51-R0 result: dynamic context baseline

Date: 2026-09-11

The corrected frozen run covered 15 cases: delayed memory, separated parity,
and reversal, each across seeds 11, 17, 23, 29, and 31. R0 beat the nonlinear
fixed-window control on 12/15 cases and matched or beat the no-history/base
control on 13/15 cases. Every case reproduced the same MAE after JSON
save/reload.

This is a positive isolated R0 result on the preregistered synthetic temporal
family, not proof that a reservoir improves Kairo's program-understanding
tasks. The reversal family is mixed and remains the main weakness. The next
required test is integration through a typed dynamic-context interface on
fresh Kairo temporal workloads, with S-only and fixed-window controls.

The first implementation run exposed and corrected a harness error: readouts
were initially trained against raw next-input values while scored against the
declared temporal targets. That run is not included as a result; the
correction is covered by the current tests and the final receipt.

Receipt: `verification/R51_R0.json`.
