# Experiment 3 - Extended Trials + Steady-State False Positives

## Part A - Updated Table 2 (LLM Response Agent, N=50, 95% Wilson CI)

Model `claude-sonnet-4-6`, N=50 per scenario. (Sourced from the Experiment 1 LLM run — same config, no repeated calls.)

| Scenario | Correct action(s) | Success rate (95% CI) | Wrong-action | Miss |
|---|---|--:|--:|--:|
| S1 Faulty Update | `ROLLBACK` | 0.980 [0.895, 0.996] | 0.000 | 0.020 |
| S2 Zone Failure | `FAILOVER` | 0.000 [0.000, 0.071] | 0.980 | 0.020 |
| S3 Memory Leak | `RESTART/SCALE_UP` | 0.680 [0.542, 0.792] | 0.000 | 0.320 |
| S4 Cascading Failure | `ISOLATE/FAILOVER` | 0.000 [0.000, 0.071] | 0.980 | 0.020 |
| **Aggregate** | — | **0.415 [0.349, 0.484] (83/200)** | 0.490 | 0.095 |

## Part B - Steady-State False Positives (zero injected failures)

- Simulated **30.0 min** (360 polls/system × 10 systems @ 5s), accelerated time.
- Healthy-noise model: CPU σ=6.0, MEM σ=6.0, benign transient spike prob=0.005 (magnitude 2.2–3.0× baseline).

| Metric | Value |
|---|--:|
| Total polls | 3600 |
| Benign transients injected | 16 |
| **False-positive alerts** | **17** |
| Escalated to Response (no gate) | 17 |
| → LLM would remediate (**false remediation**) | 6 |
| → LLM correctly abstained | 11 |
| **FP alerts / hour** | **34.0** |
| **False remediations / hour** | **12.0** |
| FP per 1000 polls | 4.72 |

## Notes

- **Every false positive escalates to a Response action attempt** — the Response agent has no confidence/consolidation gate (finding #1). The LLM is the only backstop; the false-remediation count is how often it failed to be one.
- FP rate is sensitive to the healthy-noise model above; parameters are recorded in `results.json` for reproducibility. Against the committed mock (constant healthy metrics) the FP rate is 0 — not informative.
