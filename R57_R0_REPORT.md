# R57-R0 result: broader dynamic-context validation

Date: 2026-09-11

R57 expanded the R0 nonlinear-VAR/NG-RC-style readout to 25 held-out cases:
five temporal configurations (`delayed_3`, `delayed_7`, `parity_2_5`,
`parity_3_7`, and `reversal_mid`) across five seeds. Every case used a
disjoint generated test sequence and compared constant-history base,
nonlinear fixed-window, and R0 readouts.

| Measure | Result |
|---|---:|
| R0 wins over fixed-window | 18/25 |
| R0 matches or beats base | 20/25 |
| Mean base MAE | 0.3984 |
| Mean fixed-window MAE | 0.3511 |
| Mean R0 MAE | 0.1118 |
| Exact save/reload | 25/25 |
| Maximum Python allocation | 600,880 bytes |
| Mean case time | 0.438 seconds |

The gain is concentrated in delayed-7 and parity (5/5 wins in each). R0 did
not improve delayed-3 and was mixed on reversal (3/5 wins). This is a
positive isolated R0 capability result, not proof of benefit to Kairo's
program-understanding workload.

Decision: retain R0 for integration testing, but defer integration and all
weights until a typed Kairo temporal workload reproduces the advantage against
S-only and fixed-window controls. R0 remains context/proposal input only and
cannot alter symbolic acceptance.

Receipt: `verification/R57_R0.json`; independent audit: `kairo_r57.audit`.
