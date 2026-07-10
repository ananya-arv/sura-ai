"""
Experiment 1 -- Rule-based baseline vs. LLM-powered Response Agent.

Tests the paper's unverified claim that LLM reasoning beats simple threshold
rules. Both agents receive the identical synthesized signals for every scenario;
only the decision function differs.

Metrics per scenario + aggregated:
  * Success rate with 95% Wilson CI          (action == ground-truth action)
  * Wrong-action rate                        (acted, but not the correct action)
  * Miss rate                                (took no action on a real incident)
  * Alert consolidation ratio                (alerts_in / actions_out over bursts)
  * False-positive rate -> routed to Experiment 3 (needs a no-failure steady
    state, which this harness cannot provide; every trial here is a real incident)

The rule-based side costs $0 (no API). The LLM side runs only when
LAVA_FORWARD_TOKEN is set; otherwise its columns are written as null and clearly
flagged as pending.

Usage:
  python -m experiments.exp1_rule_based.run_experiment1 [--n 50] [--seed 42]
                                                        [--with-llm] [--no-llm]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from experiments.common import scenarios as SC
from experiments.common.stats import wilson_interval
from experiments.common.llm_client import make_llm_service, DEFAULT_MODEL
from experiments.exp1_rule_based.rule_based_response_agent import (
    RuleBasedResponseAgent, RuleDecision,
)

load_dotenv()

RESULTS_DIR = Path("results/exp1_rule_based")
# Actions that count as "took no action" for miss-rate purposes.
NON_ACTIONS = {"NONE", "INVESTIGATE"}


# ===========================================================================
# Decision drivers
# ===========================================================================
def rule_decision_for(agent: RuleBasedResponseAgent, trial: SC.Trial) -> RuleDecision:
    """Primary-signal decision (single system, dedup irrelevant)."""
    agent.reset()
    if trial.is_canary:
        return agent.decide_canary(trial.canary_result)
    if trial.anomaly is None:
        return RuleDecision("NONE", "no signal tripped detection thresholds")
    return agent.decide_anomaly(trial.anomaly)


def rule_consolidation(trial: SC.Trial) -> Dict[str, int]:
    """Run the full burst through a fresh (dedup-on) agent; count in vs out."""
    if trial.is_canary or not trial.burst:
        return {"alerts_in": 0, "actions_out": 0}
    agent = RuleBasedResponseAgent(enable_dedup=True)
    agent.reset()
    actions = 0
    for alert in trial.burst:
        d = agent.decide_anomaly(alert)
        if d.action not in ("NONE",):
            actions += 1
    return {"alerts_in": len(trial.burst), "actions_out": actions}


async def llm_decision_for(trial: SC.Trial, llm):
    """
    LLM decision on the same primary signal, via the experiment Lava service.
    Returns (action, confidence, reasoning, lava_request_id) or None if the
    token is absent / the call fails.
    """
    if not llm.available:
        return None
    if not trial.is_canary and trial.anomaly is None:
        return None  # sub-threshold sample produced no signal to analyze

    if trial.is_canary:
        res = await llm.analyze_canary_deployment({
            "additional_context": {
                "update_id": trial.canary_result.update_id,
                "version": "synthetic",
                "description": "faulty-update canary trial",
                "canary_systems": 1, "total_systems": 100,
                "test_duration": 30, "errors": int(trial.error_rate * 100),
                "warnings": 0,
                "error_rate": f"{trial.error_rate:.4f}",
                "warning_rate": "0.0000",
                "latency_impact": "+0.00x",
            }
        })
    else:
        a = trial.anomaly
        res = await llm.analyze_incident({
            "alert_id": a.alert_id, "severity": a.severity,
            "system_id": a.system_id, "metric_type": a.metric_type,
            "current_value": a.current_value, "expected_value": a.expected_value,
            "confidence": a.confidence,
        })
    return (
        res.get("recommendation", "INVESTIGATE"),
        float(res.get("confidence", 0.0) or 0.0),
        res.get("reasoning", ""),
        res.get("lava_request_id", ""),
    )


# ===========================================================================
# Scoring
# ===========================================================================
def score_actions(actions: List[str], correct) -> Dict:
    """Partition per-incident actions into success / wrong / miss.

    `correct` is the scenario's set of acceptable actions (the paper lists
    compound responses, e.g. RESTART+SCALE_UP for a memory leak).
    """
    correct_set = set(correct if isinstance(correct, (list, tuple, set)) else [correct])
    n = len(actions)
    success = sum(1 for a in actions if a in correct_set)
    miss = sum(1 for a in actions if a not in correct_set and a in NON_ACTIONS)
    wrong = n - success - miss
    ci = wilson_interval(success, n)
    return {
        "n": n,
        "success": success, "wrong": wrong, "miss": miss,
        "success_rate": ci.rate,
        "success_ci_low": ci.ci_low, "success_ci_high": ci.ci_high,
        "success_ci_pretty": ci.pretty(),
        "wrong_action_rate": wrong / n if n else 0.0,
        "miss_rate": miss / n if n else 0.0,
    }


# ===========================================================================
# Main experiment
# ===========================================================================
async def run(n: int, seed: int, with_llm: bool, model: str = DEFAULT_MODEL) -> Dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RESULTS_DIR / "raw_trials.jsonl"
    raw_fh = raw_path.open("w")

    rule_agent = RuleBasedResponseAgent(enable_dedup=True)
    per_scenario: Dict[str, Dict] = {}

    llm = None
    llm_available = False
    if with_llm:
        llm = make_llm_service(model)
        llm_available = llm.available

    for scenario in SC.SCENARIO_ORDER:
        trials = SC.generate_trials(scenario, n, seed)
        correct = SC.GROUND_TRUTH[scenario]

        rule_actions: List[str] = []
        llm_actions: List[str] = []
        alerts_in = actions_out = 0
        llm_calls = 0

        for t in trials:
            rd = rule_decision_for(rule_agent, t)
            rule_actions.append(rd.action)

            cons = rule_consolidation(t)
            alerts_in += cons["alerts_in"]
            actions_out += cons["actions_out"]

            record = {
                "scenario": scenario, "trial": t.trial_index,
                "system_id": t.system_id,
                "cpu": round(t.cpu, 2), "memory": round(t.memory, 2),
                "error_rate": round(t.error_rate, 4),
                "signal": ("canary" if t.is_canary
                           else (t.anomaly.metric_type if t.anomaly else "none")),
                "rule_action": rd.action, "rule_reason": rd.reason,
                "burst_alerts": cons["alerts_in"],
                "correct_action": correct,
            }

            if llm_available:
                res = await llm_decision_for(t, llm)
                if res is not None:
                    action, conf, reasoning, rid = res
                    llm_actions.append(action)
                    llm_calls += 1
                    record.update({
                        "llm_action": action, "llm_confidence": conf,
                        "llm_reasoning": reasoning, "lava_request_id": rid,
                    })

            raw_fh.write(json.dumps(record) + "\n")

        cons_ratio = (alerts_in / actions_out) if actions_out else 0.0
        entry = {
            "label": SC.SCENARIO_LABELS[scenario],
            "correct_action": correct,
            "rule_based": score_actions(rule_actions, correct),
            "consolidation": {
                "alerts_in": alerts_in, "actions_out": actions_out,
                "ratio": cons_ratio,
            },
            "llm": (score_actions(llm_actions, correct) if llm_actions else None),
            "llm_calls": llm_calls,
        }
        per_scenario[scenario] = entry

    raw_fh.close()

    # Aggregate across scenarios (pooled counts).
    def pool(side: str) -> Optional[Dict]:
        s = w = m = tot = 0
        any_data = False
        for sc in SC.SCENARIO_ORDER:
            d = per_scenario[sc][side]
            if d is None:
                continue
            any_data = True
            s += d["success"]; w += d["wrong"]; m += d["miss"]; tot += d["n"]
        if not any_data:
            return None
        ci = wilson_interval(s, tot)
        return {
            "n": tot, "success": s, "wrong": w, "miss": m,
            "success_rate": ci.rate, "success_ci_low": ci.ci_low,
            "success_ci_high": ci.ci_high, "success_ci_pretty": ci.pretty(),
            "wrong_action_rate": w / tot if tot else 0.0,
            "miss_rate": m / tot if tot else 0.0,
        }

    config = {
        "experiment": "exp1_rule_based",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_per_scenario": n,
        "master_seed": seed,
        "llm_ran": llm_available,
        "llm_model": (model if llm_available else None),
        "paper_model": "claude-3-5-sonnet-20240620 (retired 2025-10-28)",
        "ground_truth": SC.GROUND_TRUTH,
        "ground_truth_tentative": SC.GROUND_TRUTH_IS_TENTATIVE,
        "thresholds": {
            "cpu_ratio": SC.CPU_ANOMALY_RATIO, "mem_ratio": SC.MEM_ANOMALY_RATIO,
            "error_count_limit": SC.ERROR_COUNT_LIMIT,
            "canary_rollback_er": SC.CANARY_ROLLBACK_ER,
            "canary_investigate_er": SC.CANARY_INVESTIGATE_ER,
        },
        "false_positive_note": (
            "Not measurable here: every trial is a real incident. "
            "False-positive / false-remediation rate is measured by the "
            "Experiment 3 steady-state (zero-failure) harness."
        ),
    }

    result = {
        "config": config,
        "per_scenario": per_scenario,
        "aggregate": {"rule_based": pool("rule_based"), "llm": pool("llm")},
    }

    (RESULTS_DIR / "aggregate.json").write_text(json.dumps(result, indent=2))
    _write_csv(result)
    _write_markdown(result)
    return result


def _write_csv(result: Dict) -> None:
    rows = []
    for sc in SC.SCENARIO_ORDER:
        e = result["per_scenario"][sc]
        rb = e["rule_based"]
        llm = e["llm"]
        rows.append({
            "scenario": e["label"], "correct_action": "/".join(e["correct_action"]),
            "rule_success_rate": f"{rb['success_rate']:.3f}",
            "rule_success_ci": f"[{rb['success_ci_low']:.3f},{rb['success_ci_high']:.3f}]",
            "rule_wrong_action_rate": f"{rb['wrong_action_rate']:.3f}",
            "rule_miss_rate": f"{rb['miss_rate']:.3f}",
            "consolidation_ratio": f"{e['consolidation']['ratio']:.2f}",
            "llm_success_rate": (f"{llm['success_rate']:.3f}" if llm else ""),
            "llm_wrong_action_rate": (f"{llm['wrong_action_rate']:.3f}" if llm else ""),
        })
    with (RESULTS_DIR / "summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(result: Dict) -> None:
    cfg = result["config"]
    lines: List[str] = []
    lines.append("# Experiment 1 - Rule-Based Baseline vs. LLM Response Agent\n")
    lines.append(f"- N per scenario: **{cfg['n_per_scenario']}**, seed "
                 f"`{cfg['master_seed']}`")
    llm_status = (f"yes — `{cfg['llm_model']}`" if cfg["llm_ran"]
                  else "NO (disabled or unavailable)")
    lines.append(f"- LLM side ran: **{llm_status}** "
                 f"(paper's `{cfg['paper_model']}`)")
    gt_flag = " ⚠️ TENTATIVE" if cfg["ground_truth_tentative"] else " (paper's table)"
    lines.append(f"- Ground-truth correct actions{gt_flag}: "
                 + ", ".join(f"{SC.SCENARIO_LABELS[k]}→`{'/'.join(v)}`"
                             for k, v in cfg["ground_truth"].items()))
    lines.append("")

    lines.append("## Per-scenario\n")
    lines.append("| Scenario | Correct | Rule success (95% CI) | Rule wrong-action | "
                 "Rule miss | Consolidation | LLM success (95% CI) | LLM wrong-action |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for sc in SC.SCENARIO_ORDER:
        e = result["per_scenario"][sc]
        rb, llm = e["rule_based"], e["llm"]
        llm_s = (f"{llm['success_rate']:.3f} [{llm['success_ci_low']:.3f}, "
                 f"{llm['success_ci_high']:.3f}]") if llm else "_pending token_"
        llm_w = f"{llm['wrong_action_rate']:.3f}" if llm else "_pending_"
        lines.append(
            f"| {e['label']} | `{'/'.join(e['correct_action'])}` | "
            f"{rb['success_rate']:.3f} [{rb['success_ci_low']:.3f}, {rb['success_ci_high']:.3f}] | "
            f"{rb['wrong_action_rate']:.3f} | {rb['miss_rate']:.3f} | "
            f"{e['consolidation']['ratio']:.2f}:1 | {llm_s} | {llm_w} |"
        )

    agg_rb = result["aggregate"]["rule_based"]
    agg_llm = result["aggregate"]["llm"]
    lines.append("\n## Aggregated (pooled across all four scenarios)\n")
    lines.append("| Agent | Success rate (95% Wilson CI) | Wrong-action | Miss |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Rule-based | {agg_rb['success_ci_pretty']} | "
                 f"{agg_rb['wrong_action_rate']:.3f} | {agg_rb['miss_rate']:.3f} |")
    llm_label = f"LLM ({cfg['llm_model']})" if cfg.get("llm_model") else "LLM"
    if agg_llm:
        lines.append(f"| {llm_label} | {agg_llm['success_ci_pretty']} | "
                     f"{agg_llm['wrong_action_rate']:.3f} | {agg_llm['miss_rate']:.3f} |")
    else:
        lines.append("| LLM | _pending LAVA_FORWARD_TOKEN_ | _pending_ | _pending_ |")

    lines.append("\n## Notes\n")
    lines.append("- **False-positive rate** is intentionally not reported here: every "
                 "trial is a real incident. It is measured by the Experiment 3 "
                 "steady-state (zero-failure) harness.")
    lines.append("- A per-alert threshold rule structurally cannot emit `FAILOVER`/"
                 "`ISOLATE` (needs cross-system context), so it cannot score on "
                 "scenarios whose correct action is zone-level. This is a finding, "
                 "not a bug.")
    if cfg["ground_truth_tentative"]:
        lines.append("- ⚠️ Ground-truth actions are tentative; success / wrong-action "
                     "numbers will update once the paper's Expected-behavior table is "
                     "supplied (re-scoring is free, no API calls).")
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    ap.add_argument("--with-llm", dest="with_llm", action="store_true", default=None)
    ap.add_argument("--no-llm", dest="with_llm", action="store_false")
    args = ap.parse_args()

    # Default: run LLM iff a token is present.
    with_llm = args.with_llm
    if with_llm is None:
        with_llm = bool(os.getenv("LAVA_FORWARD_TOKEN"))

    result = asyncio.run(run(args.n, args.seed, with_llm, args.model))
    print(Path(RESULTS_DIR / "summary.md").read_text())


if __name__ == "__main__":
    main()
