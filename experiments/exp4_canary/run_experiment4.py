"""
Experiment 4 -- Expanded canary testing.

The original paper ran the canary exactly once. Here we drive the REAL canary
decision path (lava_service.analyze_canary_deployment) over many synthetic
canary results spanning the decision boundary:

  case type        error-rate band     expected outcome
  ---------------  ------------------   ------------------------------------
  clean            [0.000, 0.005)       DEPLOY  (approve safe update)
  borderline       [0.005, 0.010)       ambiguous (elevated warnings, er<0.01)
  faulty_mild      [0.011, 0.030)       BLOCK   (just over the 0.01 line)
  faulty_moderate  [0.030, 0.080)       BLOCK / ROLLBACK
  faulty_severe    [0.150, 0.300)       ROLLBACK

For every trial we record the LLM decision (DEPLOY / INVESTIGATE / ROLLBACK) and
its confidence, and the pure-threshold rule's decision (canary fallback:
>0.05 ROLLBACK, >0.01 INVESTIGATE, else DEPLOY) for comparison.

Reported: prevention rate on genuinely-faulty updates, false-rollback rate on
genuinely-clean updates, confidence by case type, and the empirical decision
boundary (error rate at which the LLM flips DEPLOY->BLOCK) vs the stated 0.01.

Usage:
  python -m experiments.exp4_canary.run_experiment4 [--per-case 10] [--seed 42]
                                                     [--model claude-sonnet-4-6] [--no-llm]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from experiments.common.llm_client import make_llm_service, DEFAULT_MODEL
from experiments.common.stats import wilson_interval
from experiments.exp1_rule_based.rule_based_response_agent import RuleBasedResponseAgent
from agents.messages import CanaryTestResult

load_dotenv()
RESULTS_DIR = Path("results/exp4_canary")

# case type -> (error-rate low, high, warning_rate low, high, is_faulty, is_clean)
CASES = {
    "clean":            (0.000, 0.005, 0.00, 0.02, False, True),
    "borderline":       (0.005, 0.010, 0.05, 0.15, False, False),  # ambiguous
    "faulty_mild":      (0.011, 0.030, 0.02, 0.08, True,  False),
    "faulty_moderate":  (0.030, 0.080, 0.05, 0.15, True,  False),
    "faulty_severe":    (0.150, 0.300, 0.10, 0.30, True,  False),
}
CASE_ORDER = list(CASES.keys())
BLOCK_ACTIONS = {"ROLLBACK", "INVESTIGATE"}  # anything that stops the deploy


def _canary_result(case: str, i: int, rng: random.Random) -> CanaryTestResult:
    er_lo, er_hi, wr_lo, wr_hi, faulty, clean = CASES[case]
    er = rng.uniform(er_lo, er_hi)
    wr = rng.uniform(wr_lo, wr_hi)
    return CanaryTestResult(
        update_id=f"UPD-{case}-{i}", success=(er < 0.01),
        affected_systems=1, error_rate=er, latency_impact=rng.uniform(-0.1, 0.3),
        recommendation="", details=f"{case} synthetic canary",
    ), er, wr


async def _llm_canary(llm, cr: CanaryTestResult, er: float, wr: float) -> Dict:
    res = await llm.analyze_canary_deployment({
        "additional_context": {
            "update_id": cr.update_id, "version": "synthetic",
            "description": "canary severity-sweep trial",
            "canary_systems": 1, "total_systems": 100, "test_duration": 30,
            "errors": int(er * 3000), "warnings": int(wr * 3000),
            "error_rate": f"{er:.4f}", "warning_rate": f"{wr:.4f}",
            "latency_impact": f"{cr.latency_impact:+.2f}x",
        }
    })
    return {"action": res.get("recommendation", "INVESTIGATE"),
            "confidence": float(res.get("confidence", 0.0) or 0.0),
            "lava_request_id": res.get("lava_request_id", "")}


async def run(per_case: int, seed: int, model: str, with_llm: bool) -> Dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(hash((seed, "exp4")) & 0xFFFFFFFF)
    rule = RuleBasedResponseAgent()
    llm = make_llm_service(model) if with_llm else None
    llm_ok = bool(llm and llm.available)

    raw_fh = (RESULTS_DIR / "raw_trials.jsonl").open("w")
    # accumulators
    per_case_rows: Dict[str, List[Dict]] = {c: [] for c in CASE_ORDER}
    # boundary samples: (error_rate, llm_blocked 0/1)
    boundary: List[Dict] = []

    for case in CASE_ORDER:
        for i in range(per_case):
            cr, er, wr = _canary_result(case, i, rng)
            rule_dec = rule.decide_canary(cr).action
            row = {"case": case, "error_rate": round(er, 4), "warning_rate": round(wr, 4),
                   "rule_action": rule_dec, "llm_action": None, "llm_confidence": None}
            if llm_ok:
                d = await _llm_canary(llm, cr, er, wr)
                row["llm_action"] = d["action"]
                row["llm_confidence"] = d["confidence"]
                row["lava_request_id"] = d["lava_request_id"]
                boundary.append({"error_rate": er, "llm_blocked": int(d["action"] in BLOCK_ACTIONS)})
            per_case_rows[case].append(row)
            raw_fh.write(json.dumps(row) + "\n")
    raw_fh.close()

    result = _aggregate(per_case_rows, boundary, model if llm_ok else None, per_case, seed)
    (RESULTS_DIR / "results.json").write_text(json.dumps(result, indent=2))
    _write_markdown(result)
    try:
        from experiments.exp4_canary.plot_boundary import generate_plot
        result["_plot"] = str(generate_plot())
    except Exception as e:  # pragma: no cover
        result["_plot"] = f"skipped: {e}"
    return result


def _rate(count, n):
    return wilson_interval(count, n)


def _aggregate(rows: Dict[str, List[Dict]], boundary, model, per_case, seed) -> Dict:
    def side(row, which):  # which = 'llm' or 'rule'
        return row[f"{which}_action"]

    cases = {}
    for case, rs in rows.items():
        _, _, _, _, faulty, clean = CASES[case]
        entry = {"n": len(rs), "is_faulty": faulty, "is_clean": clean}
        for which in ("rule", "llm"):
            acts = [side(r, which) for r in rs if side(r, which) is not None]
            if not acts:
                entry[which] = None
                continue
            blocked = sum(1 for a in acts if a in BLOCK_ACTIONS)
            rolled = sum(1 for a in acts if a == "ROLLBACK")
            deployed = sum(1 for a in acts if a == "DEPLOY")
            confs = [r["llm_confidence"] for r in rs if which == "llm" and r["llm_confidence"] is not None]
            entry[which] = {
                "blocked": blocked, "rollback": rolled, "deploy": deployed,
                "block_rate": blocked / len(acts), "rollback_rate": rolled / len(acts),
                "mean_confidence": (sum(confs) / len(confs)) if confs else None,
            }
        cases[case] = entry

    # prevention rate (genuinely faulty -> should be blocked) and
    # false-rollback rate (genuinely clean -> should NOT be blocked)
    summary = {}
    for which in ("rule", "llm"):
        faulty_rows = [r for c in CASE_ORDER if CASES[c][4] for r in rows[c]]
        clean_rows = [r for c in CASE_ORDER if CASES[c][5] for r in rows[c]]
        f_acts = [r[f"{which}_action"] for r in faulty_rows if r[f"{which}_action"]]
        c_acts = [r[f"{which}_action"] for r in clean_rows if r[f"{which}_action"]]
        if not f_acts and not c_acts:
            summary[which] = None
            continue
        f_block = sum(1 for a in f_acts if a in BLOCK_ACTIONS)
        c_block = sum(1 for a in c_acts if a in BLOCK_ACTIONS)
        prev = _rate(f_block, len(f_acts)) if f_acts else None
        frr = _rate(c_block, len(c_acts)) if c_acts else None
        summary[which] = {
            "prevention_rate": (prev.as_dict() if prev else None),
            "prevention_pretty": (prev.pretty() if prev else None),
            "false_rollback_rate": (frr.as_dict() if frr else None),
            "false_rollback_pretty": (frr.pretty() if frr else None),
        }

    # empirical LLM decision boundary: highest deployed er and lowest blocked er
    boundary_note = None
    if boundary:
        deployed_ers = sorted(b["error_rate"] for b in boundary if b["llm_blocked"] == 0)
        blocked_ers = sorted(b["error_rate"] for b in boundary if b["llm_blocked"] == 1)
        boundary_note = {
            "max_error_rate_deployed": (max(deployed_ers) if deployed_ers else None),
            "min_error_rate_blocked": (min(blocked_ers) if blocked_ers else None),
            "stated_threshold": 0.01,
        }

    return {
        "config": {
            "experiment": "exp4_canary",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "per_case": per_case, "seed": seed, "llm_model": model,
            "cases": {c: {"error_rate_band": [CASES[c][0], CASES[c][1]],
                          "is_faulty": CASES[c][4], "is_clean": CASES[c][5]}
                      for c in CASE_ORDER},
        },
        "per_case": cases,
        "summary": summary,
        "decision_boundary": boundary_note,
    }


def _write_markdown(result: Dict) -> None:
    cfg = result["config"]
    lines = ["# Experiment 4 - Expanded Canary Testing\n"]
    lines.append(f"- {cfg['per_case']} trials/case × {len(CASE_ORDER)} cases "
                 f"= {cfg['per_case']*len(CASE_ORDER)} total, seed `{cfg['seed']}`, "
                 f"model `{cfg['llm_model']}`")
    lines.append("")
    lines.append("## Decision by case type (block = ROLLBACK or INVESTIGATE)\n")
    lines.append("| Case | error-rate band | LLM block-rate | LLM rollback | LLM mean conf | Rule block-rate |")
    lines.append("|---|---|--:|--:|--:|--:|")
    for c in CASE_ORDER:
        e = result["per_case"][c]
        band = f"{CASES[c][0]:.3f}–{CASES[c][1]:.3f}"
        llm = e.get("llm"); rule = e.get("rule")
        llm_b = f"{llm['block_rate']:.2f}" if llm else "—"
        llm_r = f"{llm['rollback_rate']:.2f}" if llm else "—"
        llm_c = f"{llm['mean_confidence']:.2f}" if llm and llm['mean_confidence'] is not None else "—"
        rule_b = f"{rule['block_rate']:.2f}" if rule else "—"
        lines.append(f"| {c} | {band} | {llm_b} | {llm_r} | {llm_c} | {rule_b} |")
    lines.append("")
    lines.append("## Headline rates (95% Wilson CI)\n")
    lines.append("| Agent | Prevention rate (faulty→blocked) | False-rollback rate (clean→blocked) |")
    lines.append("|---|---|---|")
    for which in ("rule", "llm"):
        s = result["summary"].get(which)
        if not s:
            continue
        lines.append(f"| {which} | {s['prevention_pretty'] or '—'} | {s['false_rollback_pretty'] or '—'} |")
    b = result.get("decision_boundary")
    if b:
        lines.append("")
        lines.append("## Empirical LLM decision boundary\n")
        lines.append(f"- Stated canary threshold: **error rate {b['stated_threshold']}**")
        lines.append(f"- Highest error rate the LLM still DEPLOYED: "
                     f"**{b['max_error_rate_deployed']}**" if b['max_error_rate_deployed'] is not None
                     else "- (no deploys)")
        lines.append(f"- Lowest error rate the LLM BLOCKED: "
                     f"**{b['min_error_rate_blocked']}**" if b['min_error_rate_blocked'] is not None
                     else "- (no blocks)")
    lines.append("")
    lines.append("See `boundary.png` for the DEPLOY/BLOCK decision vs error rate (LLM & rule).")
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-case", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    ap.add_argument("--no-llm", dest="with_llm", action="store_false", default=True)
    args = ap.parse_args()
    asyncio.run(run(args.per_case, args.seed, args.model, args.with_llm))
    print((RESULTS_DIR / "summary.md").read_text())


if __name__ == "__main__":
    main()
