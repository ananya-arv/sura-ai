# Experiment 1 - Rule-Based Baseline vs. LLM Response Agent

- N per scenario: **50**, seed `42`
- LLM side ran: **yes — `claude-sonnet-4-6`** (paper's `claude-3-5-sonnet-20240620 (retired 2025-10-28)`)
- Ground-truth correct actions (paper's table): S1 Faulty Update→`ROLLBACK`, S2 Zone Failure→`FAILOVER`, S3 Memory Leak→`RESTART/SCALE_UP`, S4 Cascading Failure→`ISOLATE/FAILOVER`

## Per-scenario

| Scenario | Correct | Rule success (95% CI) | Rule wrong-action | Rule miss | Consolidation | LLM success (95% CI) | LLM wrong-action |
|---|---|---|---|---|---|---|---|
| S1 Faulty Update | `ROLLBACK` | 0.860 [0.738, 0.930] | 0.000 | 0.140 | 0.00:1 | 0.980 [0.895, 0.996] | 0.000 |
| S2 Zone Failure | `FAILOVER` | 0.000 [0.000, 0.071] | 1.000 | 0.000 | 2.00:1 | 0.000 [0.000, 0.071] | 0.980 |
| S3 Memory Leak | `RESTART/SCALE_UP` | 1.000 [0.929, 1.000] | 0.000 | 0.000 | 1.00:1 | 0.680 [0.542, 0.792] | 0.000 |
| S4 Cascading Failure | `ISOLATE/FAILOVER` | 0.000 [0.000, 0.071] | 1.000 | 0.000 | 4.00:1 | 0.000 [0.000, 0.071] | 0.980 |

## Aggregated (pooled across all four scenarios)

| Agent | Success rate (95% Wilson CI) | Wrong-action | Miss |
|---|---|---|---|
| Rule-based | 0.465 [0.397, 0.534] (93/200) | 0.500 | 0.035 |
| LLM (claude-sonnet-4-6) | 0.415 [0.349, 0.484] (83/200) | 0.490 | 0.095 |

## Notes

- **False-positive rate** is intentionally not reported here: every trial is a real incident. It is measured by the Experiment 3 steady-state (zero-failure) harness.
- A per-alert threshold rule structurally cannot emit `FAILOVER`/`ISOLATE` (needs cross-system context), so it cannot score on scenarios whose correct action is zone-level. This is a finding, not a bug.
