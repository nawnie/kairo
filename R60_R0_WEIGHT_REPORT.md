# R60-R0 weight sweep

Date: 2026-09-11

R60 swept the contribution of the proven nonlinear-VAR R0 readout against the
fixed-window control across 25 held-out temporal cases. The blend was
`(1-weight)*fixed + weight*R0`; no symbolic Kairo acceptance decision was
changed.

| R0 weight | Mean MAE |
|---:|---:|
| 0.00 | 0.3508 |
| 0.25 | 0.2897 |
| 0.50 | 0.2285 |
| 0.75 | 0.1674 |
| 1.00 | 0.1117 |

The native temporal suite prefers full R0 contribution. This is a synthetic
native-domain result only; it does not establish the correct weight for a
Kairo program-understanding system. Real Kairo integration remains gated on a
typed dynamic-context interface and fresh program workloads.

Receipt: `verification/R60_R0_WEIGHT.json`; independent audit:
`kairo_r60_weight.audit`.
