"""
Experiment 5 -- Chain-of-thought prompting + calibration + explainability.

Runs the four scenarios under two prompt conditions (control single-shot vs CoT
step-by-step) through the same Lava model, and compares:
  * success rate (does CoT improve decision quality?)
  * confidence calibration (stated confidence vs actual accuracy; ECE + plot)
  * added latency and token/output cost from the longer CoT prompts
  * an automatic 0-2 explainability score (metric -> diagnosis -> action chain)

Every scenario is framed as an incident for analyze_incident-style prompting
(faulty_update is framed on its error rate exactly as the real Response agent's
execute_rollback_with_ai does), so both conditions use one uniform prompt path.

Cost: 4 scenarios x N x 2 conditions LLM calls. Default N=30 -> 240 calls.

Usage:
  python -m experiments.exp5_cot.run_experiment5 [--n 30] [--seed 42]
                                                 [--model claude-sonnet-4-6]
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from experiments.common import scenarios as SC
from experiments.common.stats import wilson_interval
from experiments.common.llm_client import make_llm_service, DEFAULT_MODEL, raw_json_call
from experiments.exp5_cot.prompts import control_prompt, cot_prompt, explainability_score

load_dotenv()
RESULTS_DIR = Path("results/exp5_cot")
NON_ACTIONS = {"NONE", "INVESTIGATE"}
CONDITIONS = ["control", "cot"]

# Sonnet 4.6 pricing ($/MTok) for the cost delta.
PRICE_IN, PRICE_OUT = 3.0, 15.0
# Confidence buckets for calibration.
BUCKETS = [(0.0, 0.75), (0.75, 0.85), (0.85, 0.95), (0.95, 1.0001)]


def _incident_for(trial: SC.Trial) -> Dict:
    """Uniform incident dict for both conditions."""
    if trial.is_canary:
        er = trial.error_rate
        return {
            "alert_id": f"CANARY-{trial.trial_index}",
            "severity": "CRITICAL" if er > 0.1 else "HIGH",
            "system_id": "canary_deployment", "metric_type": "ERROR_RATE",
            "current_value": er * 100, "expected_value": 1.0, "confidence": 0.95,
        }
    a = trial.anomaly
    return {
        "alert_id": a.alert_id, "severity": a.severity, "system_id": a.system_id,
        "metric_type": a.metric_type, "current_value": a.current_value,
        "expected_value": a.expected_value, "confidence": a.confidence,
    }


async def _one_call(service, condition: str, incident: Dict) -> Dict:
    prompt = (control_prompt(service, incident) if condition == "control"
              else cot_prompt(incident))
    r = await raw_json_call(service, prompt, max_tokens=1024)
    parsed = r["parsed"] or {}
    action = parsed.get("recommendation", "INVESTIGATE")
    confidence = float(parsed.get("confidence", 0.0) or 0.0)
    reasoning = parsed.get("reasoning", "") or parsed.get("root_cause", "")
    steps = parsed.get("reasoning_steps", []) if isinstance(parsed.get("reasoning_steps"), list) else []
    expl = explainability_score(action, reasoning, steps)
    return {
        "action": action, "confidence": confidence, "reasoning": reasoning,
        "n_steps": len(steps), "explainability": expl,
        "latency_s": r["latency_s"], "input_tokens": r["input_tokens"],
        "output_tokens": r["output_tokens"], "ok": r["ok"] and bool(r["parsed"]),
    }


def _bucketize(rows: List[Dict]) -> List[Dict]:
    out = []
    for lo, hi in BUCKETS:
        b = [r for r in rows if lo <= r["confidence"] < hi]
        if not b:
            out.append({"range": [lo, round(hi, 2)], "n": 0, "mean_confidence": None,
                        "accuracy": None})
            continue
        acc = sum(1 for r in b if r["success"]) / len(b)
        mc = sum(r["confidence"] for r in b) / len(b)
        out.append({"range": [lo, round(hi, 2)], "n": len(b),
                    "mean_confidence": mc, "accuracy": acc})
    return out


def _ece(rows: List[Dict]) -> float:
    n = len(rows)
    if not n:
        return 0.0
    tot = 0.0
    for b in _bucketize(rows):
        if b["n"] and b["mean_confidence"] is not None:
            tot += (b["n"] / n) * abs(b["accuracy"] - b["mean_confidence"])
    return tot


async def run(n: int, seed: int, model: str) -> Dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    service = make_llm_service(model)
    if not service.available:
        raise RuntimeError("LAVA_FORWARD_TOKEN required for Experiment 5")

    raw_fh = (RESULTS_DIR / "raw_trials.jsonl").open("w")
    by_condition: Dict[str, List[Dict]] = {c: [] for c in CONDITIONS}

    for scenario in SC.SCENARIO_ORDER:
        trials = SC.generate_trials(scenario, n, seed)
        correct = set(SC.GROUND_TRUTH[scenario])
        for t in trials:
            incident = _incident_for(t)
            for cond in CONDITIONS:
                res = await _one_call(service, cond, incident)
                res["success"] = res["action"] in correct
                rec = {"scenario": scenario, "trial": t.trial_index,
                       "condition": cond, "correct": list(correct), **res}
                raw_fh.write(json.dumps(rec) + "\n")
                by_condition[cond].append(rec)
    raw_fh.close()

    result = _aggregate(by_condition, model, n, seed)
    (RESULTS_DIR / "results.json").write_text(json.dumps(result, indent=2))
    _write_markdown(result)
    try:
        from experiments.exp5_cot.plot_calibration import generate_plot
        result["_plot"] = str(generate_plot())
    except Exception as e:  # pragma: no cover
        result["_plot"] = f"skipped: {e}"
    return result


def _cond_stats(rows: List[Dict]) -> Dict:
    n = len(rows)
    succ = sum(1 for r in rows if r["success"])
    ci = wilson_interval(succ, n)
    lat = [r["latency_s"] for r in rows]
    out_tok = [r["output_tokens"] for r in rows]
    in_tok = [r["input_tokens"] for r in rows]
    mean_out = sum(out_tok) / n if n else 0
    mean_in = sum(in_tok) / n if n else 0
    cost_per_call = (mean_in * PRICE_IN + mean_out * PRICE_OUT) / 1e6
    return {
        "n": n, "success": succ, "success_rate": ci.rate,
        "success_ci_low": ci.ci_low, "success_ci_high": ci.ci_high,
        "success_pretty": ci.pretty(),
        "mean_latency_s": sum(lat) / n if n else 0,
        "mean_output_tokens": mean_out, "mean_input_tokens": mean_in,
        "cost_per_call_usd": cost_per_call,
        "mean_explainability": sum(r["explainability"] for r in rows) / n if n else 0,
        "ece": _ece(rows),
        "calibration_buckets": _bucketize(rows),
    }


def _aggregate(by_condition, model, n, seed) -> Dict:
    stats = {c: _cond_stats(rows) for c, rows in by_condition.items()}
    ctrl, cot = stats["control"], stats["cot"]
    deltas = {
        "success_rate": cot["success_rate"] - ctrl["success_rate"],
        "mean_latency_s": cot["mean_latency_s"] - ctrl["mean_latency_s"],
        "mean_output_tokens": cot["mean_output_tokens"] - ctrl["mean_output_tokens"],
        "cost_per_call_usd": cot["cost_per_call_usd"] - ctrl["cost_per_call_usd"],
        "mean_explainability": cot["mean_explainability"] - ctrl["mean_explainability"],
        "ece": cot["ece"] - ctrl["ece"],
    }
    return {
        "config": {"experiment": "exp5_cot",
                   "generated_at": datetime.now(timezone.utc).isoformat(),
                   "n_per_scenario": n, "seed": seed, "llm_model": model,
                   "conditions": CONDITIONS},
        "stats": stats, "cot_minus_control": deltas,
    }


def _write_markdown(result: Dict) -> None:
    cfg = result["config"]
    s = result["stats"]; d = result["cot_minus_control"]
    lines = ["# Experiment 5 - Chain-of-Thought vs Single-Shot\n"]
    lines.append(f"- N={cfg['n_per_scenario']}/scenario × 4 scenarios × 2 conditions, "
                 f"seed `{cfg['seed']}`, model `{cfg['llm_model']}`")
    lines.append("")
    lines.append("| Condition | Success (95% CI) | Mean explainability (0-2) | "
                 "ECE | Mean latency | Mean out-tokens | Cost/call |")
    lines.append("|---|---|--:|--:|--:|--:|--:|")
    for c in CONDITIONS:
        st = s[c]
        lines.append(f"| {c} | {st['success_pretty']} | {st['mean_explainability']:.2f} | "
                     f"{st['ece']:.3f} | {st['mean_latency_s']:.2f}s | "
                     f"{st['mean_output_tokens']:.0f} | ${st['cost_per_call_usd']:.5f} |")
    lines.append(f"| **CoT − control** | Δ {d['success_rate']:+.3f} | "
                 f"Δ {d['mean_explainability']:+.2f} | Δ {d['ece']:+.3f} | "
                 f"Δ {d['mean_latency_s']:+.2f}s | Δ {d['mean_output_tokens']:+.0f} | "
                 f"Δ ${d['cost_per_call_usd']:+.5f} |")
    lines.append("")
    lines.append("## Calibration (stated confidence vs actual accuracy)\n")
    for c in CONDITIONS:
        lines.append(f"**{c}** (ECE = {s[c]['ece']:.3f})")
        lines.append("| confidence bucket | n | mean conf | actual accuracy |")
        lines.append("|---|--:|--:|--:|")
        for b in s[c]["calibration_buckets"]:
            if b["n"] == 0:
                continue
            lines.append(f"| {b['range'][0]:.2f}–{b['range'][1]:.2f} | {b['n']} | "
                         f"{b['mean_confidence']:.3f} | {b['accuracy']:.3f} |")
        lines.append("")
    lines.append("Lower ECE = better calibrated. See `calibration.png`.")
    lines.append("\n## Notes\n")
    lines.append("- Explainability is an automatic 0-2 rubric (metric→diagnosis→action chain); "
                 "CoT's `reasoning_steps` array is expected to raise it.")
    lines.append("- Latency/token deltas quantify the CoT overhead (ties into Experiment 2).")
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = ap.parse_args()
    asyncio.run(run(args.n, args.seed, args.model))
    print((RESULTS_DIR / "summary.md").read_text())


if __name__ == "__main__":
    main()
