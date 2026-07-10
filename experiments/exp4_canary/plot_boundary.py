"""Experiment 4 figure: canary DEPLOY/BLOCK decision vs error rate."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = Path("results/exp4_canary")
RAW = RESULTS_DIR / "raw_trials.jsonl"
OUT = RESULTS_DIR / "boundary.png"
BLOCK = {"ROLLBACK", "INVESTIGATE"}


def generate_plot() -> Path:
    rows = [json.loads(l) for l in RAW.open()]
    er = [r["error_rate"] for r in rows]
    llm_block = [1 if (r.get("llm_action") in BLOCK) else 0 for r in rows]
    rule_block = [1 if (r.get("rule_action") in BLOCK) else 0 for r in rows]
    has_llm = any(r.get("llm_action") for r in rows)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    # jitter y slightly for visibility
    import random
    rng = random.Random(0)
    if has_llm:
        ax.scatter(er, [b + rng.uniform(-0.03, 0.03) for b in llm_block],
                   c="#4C72B0", label="LLM (block=1 / deploy=0)", alpha=0.7, s=28)
    ax.scatter(er, [b + 0.08 + rng.uniform(-0.02, 0.02) for b in rule_block],
               c="#C44E52", marker="x", label="Rule threshold", alpha=0.7, s=28)
    ax.axvline(0.01, color="gray", ls="--", lw=1.5, label="stated 0.01 threshold")
    ax.set_xscale("log")
    ax.set_xlabel("canary error rate (log scale)")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["DEPLOY", "BLOCK"])
    ax.set_title("Canary decision vs error rate")
    ax.legend(loc="center left", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"Figure written: {generate_plot()}")
