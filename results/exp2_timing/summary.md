# Experiment 2 - Pipeline Timing Distributions

- Incidents: **50**, seed `42`, model `claude-sonnet-4-6`
- Monitoring poll interval: **5s** (bounds live time-to-detect; see note)

| Stage | mean | median | p90 | p99 | min | max |
|---|--:|--:|--:|--:|--:|--:|
| Detection (compute) | 69 µs | 65 µs | 144 µs | 231 µs | 1 µs | 271 µs |
| Context gathering | 11 µs | 4 µs | 23 µs | 76 µs | 0 µs | 103 µs |
| LLM latency (Lava Gateway) | 3.63 s | 3.57 s | 4.26 s | 6.45 s | 2.09 s | 7.99 s |
| Decision validation | 2 µs | 3 µs | 4 µs | 4 µs | 1 µs | 4 µs |
| Runbook execution | 1.97 s | 2.01 s | 2.01 s | 2.01 s | 1.50 s | 2.01 s |
| Communication notify | 1.1 ms | 1.1 ms | 1.6 ms | 3.4 ms | 282 µs | 3.6 ms |
| **END-TO-END** | 5.60 s | 5.55 s | 6.26 s | 8.46 s | 3.60 s | 9.99 s |

## Notes

- Reported 'detection' is threshold-compute time only. Live time-to-detect is additionally bounded by the 5s monitoring poll interval (uniform 0-interval added latency), not folded into these numbers.
- **LLM latency (Lava Gateway)** and **Runbook execution** are the two dominant real components; the orchestration stages (context gathering, validation, notification) are sub-millisecond in-process.
- Runbook durations are the agent's real `asyncio.sleep` runbook timings; they vary by action type (e.g. FAILOVER/RESTART are longer than SCALE_UP).
- Regenerate the figure: `python -m experiments.exp2_timing.plot_latency`
