"""
Experiment 3 -- Extended trials + steady-state false-positive baseline.

Part A (Table 2 update): success rate with 95% Wilson CIs at N=50 for all four
scenarios. Sourced from the Experiment 1 LLM run (identical model/seed/N), so no
LLM calls are repeated here -- reads results/exp1_rule_based/aggregate.json.

Part B (the missing measurement): steady-state false-positive / false-remediation
rate. Runs the REAL Monitoring detector against a healthy stream for an
accelerated 30-minute simulation with zero injected failures, and calls the LLM
on each false positive to see whether it remediates or abstains.

Usage:
  python -m experiments.exp3_extended.run_experiment3
      [--duration-min 30] [--interval 5] [--systems 10]
      [--transient-prob 0.005] [--seed 42] [--model claude-sonnet-4-6] [--no-llm]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

from experiments.common import scenarios as SC
from experiments.common.llm_client import make_llm_service, DEFAULT_MODEL
from experiments.exp3_extended.steady_state import run_steady_state

load_dotenv()
RESULTS_DIR = Path("results/exp3_extended")
EXP1_AGG = Path("results/exp1_rule_based/aggregate.json")


def _load_table2() -> Optional[Dict]:
    """Per-scenario LLM success + CI from the Exp 1 run (the updated Table 2)."""
    if not EXP1_AGG.exists():
        return None
    data = json.loads(EXP1_AGG.read_text())
    if data.get("config", {}).get("llm_model") is None:
        return None
    out = {"model": data["config"]["llm_model"], "n_per_scenario": data["config"]["n_per_scenario"],
           "scenarios": {}, "aggregate": data["aggregate"].get("llm")}
    for sc in SC.SCENARIO_ORDER:
        e = data["per_scenario"].get(sc, {})
        out["scenarios"][sc] = {"label": e.get("label", sc),
                                "correct_action": e.get("correct_action"),
                                "llm": e.get("llm")}
    return out


async def run(args) -> Dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cycles = int(args.duration_min * 60 / args.interval)

    llm = None
    if args.with_llm:
        llm = make_llm_service(args.model)
        if not llm.available:
            llm = None

    steady = await run_steady_state(
        n_systems=args.systems, cycles=cycles, interval_s=args.interval,
        cpu_sigma=args.cpu_sigma, mem_sigma=args.mem_sigma,
        transient_prob=args.transient_prob,
        transient_mult_range=(2.2, 3.0), seed=args.seed, llm=llm,
    )

    table2 = _load_table2()

    result = {
        "config": {
            "experiment": "exp3_extended",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_model": (args.model if llm else None),
            "table2_source": ("results/exp1_rule_based/aggregate.json"
                              if table2 else "MISSING - run Experiment 1 first"),
        },
        "table2_extended_trials": table2,
        "steady_state_false_positive": {k: v for k, v in steady.items() if k != "events"},
    }
    (RESULTS_DIR / "results.json").write_text(json.dumps(result, indent=2))
    # events separately (can be large)
    with (RESULTS_DIR / "steady_state_events.jsonl").open("w") as fh:
        for ev in steady["events"]:
            fh.write(json.dumps(ev) + "\n")
    _write_markdown(result)
    return result


def _write_markdown(result: Dict) -> None:
    cfg = result["config"]
    t2 = result["table2_extended_trials"]
    ss = result["steady_state_false_positive"]
    p, tot, rates = ss["params"], ss["totals"], ss["rates"]

    lines = ["# Experiment 3 - Extended Trials + Steady-State False Positives\n"]

    # Part A
    lines.append("## Part A - Updated Table 2 (LLM Response Agent, N=50, 95% Wilson CI)\n")
    if t2 and t2.get("scenarios"):
        lines.append(f"Model `{t2['model']}`, N={t2['n_per_scenario']} per scenario. "
                     "(Sourced from the Experiment 1 LLM run — same config, no repeated calls.)\n")
        lines.append("| Scenario | Correct action(s) | Success rate (95% CI) | Wrong-action | Miss |")
        lines.append("|---|---|--:|--:|--:|")
        for sc in SC.SCENARIO_ORDER:
            e = t2["scenarios"][sc]
            llm = e["llm"]
            ca = "/".join(e["correct_action"]) if isinstance(e["correct_action"], list) else e["correct_action"]
            if llm:
                lines.append(f"| {e['label']} | `{ca}` | "
                             f"{llm['success_rate']:.3f} [{llm['success_ci_low']:.3f}, "
                             f"{llm['success_ci_high']:.3f}] | {llm['wrong_action_rate']:.3f} | "
                             f"{llm['miss_rate']:.3f} |")
        agg = t2.get("aggregate")
        if agg:
            lines.append(f"| **Aggregate** | — | **{agg['success_ci_pretty']}** | "
                         f"{agg['wrong_action_rate']:.3f} | {agg['miss_rate']:.3f} |")
    else:
        lines.append("_Table 2 pending — run Experiment 1 with the LLM first._")
    lines.append("")

    # Part B
    lines.append("## Part B - Steady-State False Positives (zero injected failures)\n")
    lines.append(f"- Simulated **{p['sim_minutes']} min** ({p['cycles']} polls/system × "
                 f"{p['n_systems']} systems @ {p['interval_s']}s), accelerated time.")
    lines.append(f"- Healthy-noise model: CPU σ={p['cpu_sigma']}, MEM σ={p['mem_sigma']}, "
                 f"benign transient spike prob={p['transient_prob']} "
                 f"(magnitude {p['transient_mult_range'][0]}–{p['transient_mult_range'][1]}× baseline).")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|--:|")
    lines.append(f"| Total polls | {tot['total_polls']} |")
    lines.append(f"| Benign transients injected | {tot['transients_injected']} |")
    lines.append(f"| **False-positive alerts** | **{tot['false_positive_alerts']}** |")
    lines.append(f"| Escalated to Response (no gate) | {tot['escalated_to_response']} |")
    lines.append(f"| → LLM would remediate (**false remediation**) | {tot['llm_false_remediations']} |")
    lines.append(f"| → LLM correctly abstained | {tot['llm_correctly_abstained']} |")
    lines.append(f"| **FP alerts / hour** | **{rates['fp_alerts_per_hour']:.1f}** |")
    lines.append(f"| **False remediations / hour** | **{rates['false_remediations_per_hour']:.1f}** |")
    lines.append(f"| FP per 1000 polls | {rates['fp_per_1000_polls']:.2f} |")
    lines.append("")
    lines.append("## Notes\n")
    lines.append("- **Every false positive escalates to a Response action attempt** — the "
                 "Response agent has no confidence/consolidation gate (finding #1). The LLM "
                 "is the only backstop; the false-remediation count is how often it failed to "
                 "be one.")
    lines.append("- FP rate is sensitive to the healthy-noise model above; parameters are "
                 "recorded in `results.json` for reproducibility. Against the committed mock "
                 "(constant healthy metrics) the FP rate is 0 — not informative.")
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-min", type=float, default=30.0)
    ap.add_argument("--interval", type=int, default=5)
    ap.add_argument("--systems", type=int, default=10)
    ap.add_argument("--cpu-sigma", type=float, default=6.0)
    ap.add_argument("--mem-sigma", type=float, default=6.0)
    ap.add_argument("--transient-prob", type=float, default=0.005)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    ap.add_argument("--no-llm", dest="with_llm", action="store_false", default=True)
    args = ap.parse_args()
    asyncio.run(run(args))
    print((RESULTS_DIR / "summary.md").read_text())


if __name__ == "__main__":
    main()
