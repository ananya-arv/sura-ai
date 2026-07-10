"""Experiment 5 calibration figure: stated confidence vs actual accuracy."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = Path("results/exp5_cot")
RESULTS = RESULTS_DIR / "results.json"
OUT = RESULTS_DIR / "calibration.png"
COLORS = {"control": "#4C72B0", "cot": "#55A868"}


def generate_plot() -> Path:
    data = json.loads(RESULTS.read_text())
    stats = data["stats"]

    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.plot([0, 1], [0, 1], ls="--", color="gray", lw=1, label="perfect calibration")
    for cond, st in stats.items():
        xs, ys, sizes = [], [], []
        for b in st["calibration_buckets"]:
            if b["n"] and b["mean_confidence"] is not None:
                xs.append(b["mean_confidence"]); ys.append(b["accuracy"])
                sizes.append(20 + b["n"] * 4)
        if xs:
            ax.plot(xs, ys, "-o", color=COLORS.get(cond, None),
                    label=f"{cond} (ECE={st['ece']:.3f})")
            ax.scatter(xs, ys, s=sizes, color=COLORS.get(cond, None), alpha=0.5)
    ax.set_xlim(0.5, 1.02); ax.set_ylim(0, 1.02)
    ax.set_xlabel("stated confidence"); ax.set_ylabel("actual accuracy")
    ax.set_title("Confidence calibration: CoT vs single-shot")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"Figure written: {generate_plot()}")
