"""
Experiment 2 -- Timing instrumentation.

Replaces the paper's "~30-60s / 2-5min / 5-15s" estimates with measured
distributions for every pipeline stage. Runs N incidents (mixed across the four
scenarios so runbook-action variety is represented), timing each stage with a
monotonic clock, and reports per-stage and end-to-end mean/median/p90/p99/min/max.

Requires LAVA_FORWARD_TOKEN (measures real Lava latency). Cost ~ N LLM calls.

Methodological note written into the summary: monitoring *detection* here is the
threshold-compute time only (sub-ms). In the live system, time-to-detect is
additionally bounded by the 5s monitoring poll interval
(config.MONITORING_INTERVAL) -- that bound is reported separately, not folded
into these pipeline latencies.

Usage:
  python -m experiments.exp2_timing.run_experiment2 [--n 50] [--seed 42]
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
from experiments.common.stats import summarize_latencies
from experiments.common.llm_client import make_llm_service, DEFAULT_MODEL
from experiments.exp2_timing.instrumented_pipeline import (
    run_incident, make_runbook_holder, DURATION_SPEC,
)

load_dotenv()
RESULTS_DIR = Path("results/exp2_timing")

# Order stages report in (pipeline order, end_to_end last).
REPORT_ORDER = ["detection", "context_gathering", "llm_lava", "validation",
                "runbook", "notification", "end_to_end"]

STAGE_LABEL = {
    "detection": "Detection (compute)",
    "context_gathering": "Context gathering",
    "llm_lava": "LLM latency (Lava Gateway)",
    "validation": "Decision validation",
    "runbook": "Runbook execution",
    "notification": "Communication notify",
    "end_to_end": "END-TO-END",
}


def _build_incidents(n: int, seed: int) -> List[SC.Trial]:
    """N incidents round-robined across scenarios for action-type variety."""
    per = {sc: SC.generate_trials(sc, n, seed) for sc in SC.SCENARIO_ORDER}
    incidents: List[SC.Trial] = []
    i = 0
    while len(incidents) < n:
        sc = SC.SCENARIO_ORDER[i % len(SC.SCENARIO_ORDER)]
        idx = i // len(SC.SCENARIO_ORDER)
        if idx < len(per[sc]):
            incidents.append(per[sc][idx])
        i += 1
        if i > n * len(SC.SCENARIO_ORDER) + 10:
            break
    return incidents[:n]


async def run(n: int, seed: int, model: str) -> Dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    llm = make_llm_service(model)
    if not llm.available:
        raise RuntimeError("LAVA_FORWARD_TOKEN required for Experiment 2 (measures real Lava latency)")

    runbook_holder = make_runbook_holder()
    status_path = RESULTS_DIR / "_last_status.json"
    incidents = _build_incidents(n, seed)

    events_fh = (RESULTS_DIR / "events.jsonl").open("w")
    per_stage: Dict[str, List[float]] = {k: [] for k in DURATION_SPEC}

    for t in incidents:
        rec = await run_incident(t, llm, runbook_holder, status_path)
        events_fh.write(json.dumps(rec) + "\n")
        for stage, val in rec["durations_s"].items():
            per_stage[stage].append(val)
    events_fh.close()

    stage_stats = {stage: summarize_latencies(vals) for stage, vals in per_stage.items()}

    from config import config as sura_config
    monitoring_interval = getattr(sura_config, "MONITORING_INTERVAL", 5)

    result = {
        "config": {
            "experiment": "exp2_timing",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "n_incidents": len(incidents),
            "master_seed": seed,
            "llm_model": model,
            "paper_model": "claude-3-5-sonnet-20240620 (retired 2025-10-28)",
            "monitoring_poll_interval_s": monitoring_interval,
            "detection_note": (
                "Reported 'detection' is threshold-compute time only. Live "
                f"time-to-detect is additionally bounded by the {monitoring_interval}s "
                "monitoring poll interval (uniform 0-interval added latency), not "
                "folded into these numbers."
            ),
        },
        "stage_stats": stage_stats,
    }
    (RESULTS_DIR / "aggregate.json").write_text(json.dumps(result, indent=2))
    _write_markdown(result)
    return result


def _fmt_ms(seconds: float) -> str:
    ms = seconds * 1000.0
    if ms >= 1000:
        return f"{seconds:.2f} s"
    if ms >= 1:
        return f"{ms:.1f} ms"
    return f"{ms*1000:.0f} µs"


def _write_markdown(result: Dict) -> None:
    cfg = result["config"]
    ss = result["stage_stats"]
    lines: List[str] = []
    lines.append("# Experiment 2 - Pipeline Timing Distributions\n")
    lines.append(f"- Incidents: **{cfg['n_incidents']}**, seed `{cfg['master_seed']}`, "
                 f"model `{cfg['llm_model']}`")
    lines.append(f"- Monitoring poll interval: **{cfg['monitoring_poll_interval_s']}s** "
                 "(bounds live time-to-detect; see note)")
    lines.append("")
    lines.append("| Stage | mean | median | p90 | p99 | min | max |")
    lines.append("|---|--:|--:|--:|--:|--:|--:|")
    for stage in REPORT_ORDER:
        s = ss.get(stage)
        if not s or s["n"] == 0:
            continue
        bold = stage == "end_to_end"
        label = STAGE_LABEL[stage]
        if bold:
            label = f"**{label}**"
        lines.append(
            f"| {label} | {_fmt_ms(s['mean'])} | {_fmt_ms(s['median'])} | "
            f"{_fmt_ms(s['p90'])} | {_fmt_ms(s['p99'])} | {_fmt_ms(s['min'])} | "
            f"{_fmt_ms(s['max'])} |"
        )
    lines.append("")
    lines.append("## Notes\n")
    lines.append(f"- {cfg['detection_note']}")
    lines.append("- **LLM latency (Lava Gateway)** and **Runbook execution** are the two "
                 "dominant real components; the orchestration stages (context gathering, "
                 "validation, notification) are sub-millisecond in-process.")
    lines.append("- Runbook durations are the agent's real `asyncio.sleep` runbook timings; "
                 "they vary by action type (e.g. FAILOVER/RESTART are longer than SCALE_UP).")
    lines.append("- Regenerate the figure: "
                 "`python -m experiments.exp2_timing.plot_latency`")
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = ap.parse_args()
    asyncio.run(run(args.n, args.seed, args.model))
    print((RESULTS_DIR / "summary.md").read_text())
    # Best-effort figure generation (skips cleanly if matplotlib missing).
    try:
        from experiments.exp2_timing.plot_latency import generate_plot
        out = generate_plot()
        print(f"\nFigure written: {out}")
    except Exception as e:  # pragma: no cover
        print(f"(plot skipped: {e})")


if __name__ == "__main__":
    main()
