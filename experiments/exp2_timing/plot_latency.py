"""
Regenerate the Experiment 2 latency figure (paper-ready PNG) from events.jsonl.

Standalone and headless (Agg backend). Run:
  python -m experiments.exp2_timing.plot_latency
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = Path("results/exp2_timing")
EVENTS = RESULTS_DIR / "events.jsonl"
OUT = RESULTS_DIR / "latency_distributions.png"

# Stages shown in the box plot (skip end_to_end; it dwarfs the rest).
BOX_STAGES = ["detection", "context_gathering", "llm_lava", "validation",
              "runbook", "notification"]
BOX_LABEL = {
    "detection": "detect", "context_gathering": "context", "llm_lava": "LLM/Lava",
    "validation": "validate", "runbook": "runbook", "notification": "notify",
}


def _load() -> List[Dict]:
    if not EVENTS.exists():
        raise FileNotFoundError(f"{EVENTS} not found -- run run_experiment2 first")
    return [json.loads(l) for l in EVENTS.open()]


def generate_plot() -> Path:
    events = _load()
    e2e = [ev["durations_s"]["end_to_end"] for ev in events if "end_to_end" in ev["durations_s"]]
    lava = [ev["durations_s"]["llm_lava"] for ev in events if "llm_lava" in ev["durations_s"]]
    by_stage = {s: [ev["durations_s"][s] for ev in events if s in ev["durations_s"]]
                for s in BOX_STAGES}
    # mean contribution of each stage to end-to-end
    mean_contrib = {s: (sum(v) / len(v) if v else 0.0) for s, v in by_stage.items()}

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle(f"Sura.ai pipeline latency (N={len(events)} incidents)", fontsize=13)

    # A) end-to-end histogram
    ax = axes[0][0]
    ax.hist(e2e, bins=min(20, max(5, len(e2e) // 3)), color="#4C72B0", edgecolor="white")
    ax.set_title("End-to-end resolution time")
    ax.set_xlabel("seconds"); ax.set_ylabel("incidents")
    if e2e:
        med = sorted(e2e)[len(e2e) // 2]
        ax.axvline(med, color="#C44E52", ls="--", lw=1.5, label=f"median {med:.2f}s")
        ax.legend()

    # B) Lava latency histogram
    ax = axes[0][1]
    ax.hist(lava, bins=min(20, max(5, len(lava) // 3)), color="#55A868", edgecolor="white")
    ax.set_title("LLM latency (Lava Gateway call)")
    ax.set_xlabel("seconds"); ax.set_ylabel("incidents")
    if lava:
        med = sorted(lava)[len(lava) // 2]
        ax.axvline(med, color="#C44E52", ls="--", lw=1.5, label=f"median {med:.2f}s")
        ax.legend()

    # C) per-stage box plot (log scale; stages span µs to seconds)
    ax = axes[1][0]
    data = [by_stage[s] for s in BOX_STAGES]
    ax.boxplot(data, tick_labels=[BOX_LABEL[s] for s in BOX_STAGES], showfliers=False)
    ax.set_yscale("log")
    ax.set_title("Per-stage duration (log scale)")
    ax.set_ylabel("seconds")
    ax.tick_params(axis="x", rotation=30)

    # D) mean stage contribution (stacked single bar)
    ax = axes[1][1]
    bottom = 0.0
    colors = ["#8172B3", "#CCB974", "#55A868", "#64B5CD", "#C44E52", "#937860"]
    for s, c in zip(BOX_STAGES, colors):
        val = mean_contrib[s]
        ax.bar(0, val, bottom=bottom, color=c, label=f"{BOX_LABEL[s]} ({val*1000:.0f} ms)")
        bottom += val
    ax.set_title("Mean stage contribution to end-to-end")
    ax.set_ylabel("seconds")
    ax.set_xticks([])
    ax.legend(fontsize=8, loc="upper right")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"Figure written: {generate_plot()}")
