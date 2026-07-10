# Experiment 5 - Chain-of-Thought vs Single-Shot

- N=30/scenario × 4 scenarios × 2 conditions, seed `42`, model `claude-sonnet-4-6`

| Condition | Success (95% CI) | Mean explainability (0-2) | ECE | Mean latency | Mean out-tokens | Cost/call |
|---|---|--:|--:|--:|--:|--:|
| control | 0.492 [0.404, 0.580] (59/120) | 1.49 | 0.433 | 3.75s | 130 | $0.00253 |
| cot | 0.467 [0.380, 0.556] (56/120) | 1.93 | 0.434 | 8.22s | 331 | $0.00579 |
| **CoT − control** | Δ -0.025 | Δ +0.43 | Δ +0.001 | Δ +4.47s | Δ +200 | Δ $+0.00326 |

## Calibration (stated confidence vs actual accuracy)

**control** (ECE = 0.433)
| confidence bucket | n | mean conf | actual accuracy |
|---|--:|--:|--:|
| 0.85–0.95 | 90 | 0.883 | 0.322 |
| 0.95–1.00 | 30 | 0.950 | 1.000 |

**cot** (ECE = 0.434)
| confidence bucket | n | mean conf | actual accuracy |
|---|--:|--:|--:|
| 0.75–0.85 | 5 | 0.820 | 0.000 |
| 0.85–0.95 | 89 | 0.862 | 0.337 |
| 0.95–1.00 | 26 | 0.952 | 1.000 |

Lower ECE = better calibrated. See `calibration.png`.

## Notes

- Explainability is an automatic 0-2 rubric (metric→diagnosis→action chain); CoT's `reasoning_steps` array is expected to raise it.
- Latency/token deltas quantify the CoT overhead (ties into Experiment 2).
