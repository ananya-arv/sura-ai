# Sura.ai — Paper Extension: Experiment Results

Model: **claude-sonnet-4-6** (the paper's `claude-3-5-sonnet-20240620` was retired
2025-10-28; its same-tier successor was evaluated through the same Lava gateway).
Seed **42**, direct in-process harness, Wilson 95% CIs. All original agent/
scenario code is untouched; new code lives under `experiments/`.

> **Experiment 1 (rule-based vs LLM) is excluded from this analysis by author
> decision.** Its artifacts remain on disk (`results/exp1_rule_based/`) because
> Experiment 3's Table 2 sources the LLM Response-Agent numbers from that run.

> **⚠️ Cross-cutting caveat (Zone Failure & Cascading).** The harness delivers the
> Response Agent a *single* AnomalyAlert per incident. The paper's activation
> sequence for those two scenarios has the agent *"gather zone context"* before
> the LLM decides — which this harness does not provide. Consequently the LLM
> cannot recommend the zone-level actions the ground truth requires (`FAILOVER`,
> `ISOLATE`) and scores ~0% on S2/S4 in Table 2 (Exp 3A), which in turn depresses
> the Exp 5 accuracy/calibration numbers. This is a harness limitation, not
> necessarily an LLM limitation. Fixing it (injecting zone context) is the
> recommended follow-up.

---

## Experiment 2 — Pipeline timing distributions

**What ran:** 50 incidents mixed across the four scenarios, each driven through
an instrumented pipeline that reuses the *real* components — the real detection
threshold logic, the real Lava LLM call, and the real runbook coroutines (with
their actual `asyncio.sleep` timings). Every stage boundary timestamped with a
monotonic clock.

**Results** (`results/exp2_timing/summary.md`, figure `latency_distributions.png`):

| Stage | median | p99 |
|---|--:|--:|
| Detection (compute) | 65 µs | 231 µs |
| LLM latency (Lava Gateway) | 3.57 s | 6.45 s |
| Runbook execution | 2.01 s | 2.01 s |
| **End-to-end** | **5.55 s** | **8.46 s** |

**Surprising finding:** measured end-to-end resolution is **~5.6 s**, versus the
paper's "~2–5 minutes" estimate — an overestimate of **30–50×**. The pipeline is
dominated by two real components: the Lava/LLM call (~3.6 s) and runbook
execution (~2 s); all orchestration stages are sub-millisecond. Live
*time-to-detect* additionally carries the 5 s monitoring poll interval, reported
separately rather than folded in.

---

## Experiment 3 — Extended trials + steady-state false positives

### Part A — Updated Table 2 (LLM Response Agent, N=50, 95% Wilson CI)

Sourced from the Exp 1 LLM run (same config; no repeated calls).

| Scenario | Correct action(s) | Success (95% CI) | Miss |
|---|---|--:|--:|
| S1 Faulty Update | ROLLBACK | 0.980 [0.895, 0.996] | 0.020 |
| S2 Zone Failure | FAILOVER | 0.000 [0.000, 0.071] | 0.020 |
| S3 Memory Leak | RESTART/SCALE_UP | 0.680 [0.542, 0.792] | 0.320 |
| S4 Cascading Failure | ISOLATE/FAILOVER | 0.000 [0.000, 0.071] | 0.020 |
| **Aggregate** | — | **0.415 [0.349, 0.484]** | 0.095 |

The 0% on S2/S4 is the single-alert caveat above. S1 is strong; on S3 the LLM
abstains (`INVESTIGATE`) ~32% of the time.

### Part B — Steady-state false positives (the measurement the paper was missing)

**What ran:** the *real* stateful `MonitoringAgent.detect_anomaly` (per-system
learned baseline + EMA) over an accelerated 30-min simulation (3,600 polls) with
**zero injected failures**, on a healthy stream with benign transient load spikes
(prob 0.005, 2.2–3.0× baseline). The LLM was called on every false positive to
test whether it acts as a backstop.

| Metric | Value |
|---|--:|
| False-positive alerts | **17** |
| Escalated to a Response action attempt (no gate) | **17 (100%)** |
| → LLM would remediate (false remediation) | 6 |
| → LLM correctly abstained | 11 |
| **FP alerts / hour** | **34.0** |
| **False remediations / hour** | **12.0** |

**Surprising findings:** (1) the naive `cpu > 2× baseline` rule flags **100% of
benign transients**; (2) because the Response Agent has **no confidence or
consolidation gate**, *every* false positive escalates to an action attempt — the
LLM is the only backstop, and it lets **~35% (6/17)** through, i.e. **~12 false
remediations per hour** of healthy operation. FP rate is sensitive to the
healthy-noise model (parameters recorded in `results.json`); against the
committed mock, which has constant healthy metrics, the FP rate is trivially 0.

---

## Experiment 4 — Expanded canary testing

**What ran:** 50 canary decisions (10 each across 5 error-rate bands) through the
real canary LLM path, with the pure-threshold rule for comparison.
(`results/exp4_canary/summary.md`, figure `boundary.png`.)

| Case | error-rate band | LLM block-rate | Rule block-rate |
|---|---|--:|--:|
| clean | 0.000–0.005 | **0.60** | 0.00 |
| borderline | 0.005–0.010 | 1.00 | 0.00 |
| faulty (mild→severe) | 0.011–0.300 | 1.00 | 1.00 |

| Agent | Prevention rate (faulty→blocked) | False-rollback rate (clean→blocked) |
|---|---|---|
| Rule | 1.000 [0.886, 1.000] | 0.000 [0.000, 0.278] |
| LLM | 1.000 [0.886, 1.000] | **0.600 [0.313, 0.832]** |

**Surprising findings:** both catch **100%** of genuinely faulty updates. But the
LLM's effective decision boundary sits far *below* the stated 0.01 threshold —
it blocked updates with error rates as low as **0.0003** and never deployed
anything above **0.0027**. The result is a **60% false-rollback rate on
genuinely clean updates** (vs 0% for the rule): the LLM is markedly
over-conservative, blocking safe deployments. This extends the paper's single
"Canary Tests Run: 1" line into a real evaluation and shows the canary's real
weakness is false rollbacks, not missed catches.

---

## Experiment 5 — Chain-of-thought prompting + calibration

**What ran:** all four scenarios under control (single-shot) vs CoT (forced
step-by-step) prompting, N=30 each → 240 LLM calls. Automatic 0–2 explainability
rubric, confidence calibration, and latency/token overhead.
(`results/exp5_cot/summary.md`, figure `calibration.png`.)

| Condition | Success (95% CI) | Explainability (0–2) | ECE | Mean latency | Cost/call |
|---|---|--:|--:|--:|--:|
| control | 0.492 [0.404, 0.580] | 1.49 | 0.433 | 3.75 s | $0.00253 |
| CoT | 0.467 [0.380, 0.556] | 1.93 | 0.434 | 8.22 s | $0.00579 |
| **CoT − control** | **Δ −0.025** | **Δ +0.43** | Δ +0.001 | **Δ +4.47 s** | **Δ +$0.0033** |

**Surprising findings:** CoT **does not improve decision quality** (Δ −0.025,
CIs overlap) and **does not improve calibration** (ECE identical). Its only clear
gain is **explainability (+0.43 on the 0–2 rubric)** — bought at **2.2× latency,
2.5× tokens, 2.3× cost**. Both conditions are **badly over-confident**: in the
0.85–0.95 stated-confidence bucket (90 of 120 predictions) actual accuracy is
only **~0.33**; only the 0.95–1.0 bucket is well-calibrated. *Caveat:* this
accuracy/calibration is depressed by the S2/S4 single-alert artifact — the
overconfidence is real but its magnitude is inflated by the harness limitation.

---

## Where everything lives

| Experiment | Code | Results | Figure |
|---|---|---|---|
| 2 Timing | `experiments/exp2_timing/` | `results/exp2_timing/` | `latency_distributions.png` |
| 3 Extended + FP | `experiments/exp3_extended/` | `results/exp3_extended/` | — |
| 4 Canary | `experiments/exp4_canary/` | `results/exp4_canary/` | `boundary.png` |
| 5 CoT | `experiments/exp5_cot/` | `results/exp5_cot/` | `calibration.png` |

Every experiment writes raw per-trial JSONL, a machine-readable `results.json`/
`aggregate.json`, and a `summary.md`. All runs are seeded (42) and reproducible;
re-run any via `python -m experiments.<exp>.<runner>`.

## Recommended follow-ups
1. **Inject zone context** for Zone/Cascading so the LLM can reach `FAILOVER`/
   `ISOLATE` — the fair test the current harness doesn't provide (affects Exp 3A
   and Exp 5).
2. **Add a confidence/consolidation gate** to the Response Agent and re-measure
   Exp 3B false-remediation rate — currently there is none (finding #1).
3. **Tune the canary decision boundary** — the LLM's ~0.003 effective threshold
   causes a 60% false-rollback rate on clean updates (Exp 4).
