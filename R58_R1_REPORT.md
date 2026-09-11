# R58-R1 result: actual recurrent reservoir

Date: 2026-09-11

This is separate from R57's nonlinear-VAR result. R1 implements the actual
leaky recurrent update

`x_t = (1-leak)x_(t-1) + leak*tanh(W_res x_(t-1) + W_in u_t + b)`

with seeded sparse recurrent weights, washout, and a ridge readout. It was
compared with constant-history and existing fixed-window controls on 30 cases:
six temporal configurations × five seeds, including an unseen-delay case.

| Measure | Result |
|---|---:|
| R1 wins over fixed-window | 17/30 |
| R1 matches or beats base | 22/30 |
| Mean base MAE | 0.3725 |
| Mean fixed-window MAE | 0.3322 |
| Mean R1 MAE | 0.3578 |
| Exact save/reload | 30/30 |
| Maximum peak RSS | 20,426,752 bytes |
| Maximum Python allocation | 351,996 bytes |

R1 helps delayed-7 and both parity families, but loses on delayed-3,
unseen-delay, and reversal. Its overall mean is worse than the simpler
fixed-window control.

Decision: defer R1 integration and assign no Kairo weight. Do not discard the
reservoir research direction entirely; the current topology/leak/readout
configuration has not earned promotion. Preserve R57's nonlinear-VAR result
as the stronger R0 baseline and test any future reservoir change against this
receipt.

Receipt: `verification/R58_R1.json`; independent audit: `kairo_r1.audit`.
