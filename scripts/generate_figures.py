#!/usr/bin/env python3
"""
CDR Figures — charts built from measured data only.

Produces:
    eval/results/fig_runs.png   End-to-end wall-clock time of the bundled real runs

Data source: the `metadata` block of every
examples/output/online/run_*/sample_report_online.json, written by the run
script at the time of the run. Nothing in this file is typed in by hand.

Per-stage timing is not recorded yet (see `stage_latencies` in
eval/eval_runner.py), so there is no per-stage chart. When it is, add one here.

Usage:
    make figures
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "examples" / "output" / "online"
OUT_PATH = ROOT / "eval" / "results" / "fig_runs.png"

# Dark surface to match docs/assets; hues validated for CVD separation on it.
SURFACE = "#0f172a"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
GRID = "#1e293b"
PROVIDER_COLORS = {"groq": "#3987e5", "openrouter": "#d95926"}


def load_runs() -> list[dict]:
    """Collect measured metadata from every bundled online run."""
    runs = []
    for path in sorted(RUNS_DIR.glob("run_*/sample_report_online.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        meta = report.get("metadata") or {}
        if "latency_seconds" not in meta:
            continue
        runs.append(
            {
                "run": path.parent.name,
                "question": report.get("question", ""),
                "provider": meta.get("provider", "unknown"),
                "model": meta.get("model", "unknown"),
                "minutes": meta["latency_seconds"] / 60,
                "studies": report.get("study_count", 0),
                "claims": report.get("claim_count", 0),
            }
        )
    return runs


def short_question(q: str, width: int = 62) -> str:
    return q if len(q) <= width else q[: width - 1].rstrip() + "…"


def generate_runs_chart(runs: list[dict]) -> Path:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except ImportError:
        print("❌  matplotlib not installed. Run: make setup")
        sys.exit(1)

    runs = sorted(runs, key=lambda r: r["minutes"])
    labels = [short_question(r["question"]) for r in runs]
    values = [r["minutes"] for r in runs]
    colors = [PROVIDER_COLORS.get(r["provider"], TEXT_SECONDARY) for r in runs]

    fig, ax = plt.subplots(figsize=(11.5, 0.62 * len(runs) + 1.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    bars = ax.barh(labels, values, color=colors, height=0.55, edgecolor=SURFACE, linewidth=2)
    for bar, r in zip(bars, runs, strict=True):
        ax.text(
            bar.get_width() + 0.4,
            bar.get_y() + bar.get_height() / 2,
            f"{r['minutes']:.0f} min · {r['studies']} studies · {r['claims']} claims",
            va="center",
            fontsize=9,
            color=TEXT_SECONDARY,
        )

    ax.set_xlabel("Wall-clock time per run (minutes)", color=TEXT_SECONDARY, fontsize=10)
    ax.set_xlim(0, max(values) * 1.45)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.tick_params(axis="y", colors=TEXT_PRIMARY, length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)

    models = {r["provider"]: r["model"] for r in runs}
    ax.legend(
        handles=[
            Patch(color=PROVIDER_COLORS[p], label=f"{p} · {models[p]}")
            for p in PROVIDER_COLORS
            if p in models
        ],
        loc="lower right",
        frameon=True,
        facecolor=SURFACE,
        edgecolor=SURFACE,
        framealpha=1.0,
        fontsize=9,
        labelcolor=TEXT_SECONDARY,
    )

    fig.subplots_adjust(left=0.385, right=0.98, top=0.84)
    fig.text(
        0.01,
        0.97,
        "Real CDR runs: end-to-end time on free-tier 8B models",
        color=TEXT_PRIMARY,
        fontsize=13,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.01,
        0.915,
        "Measured, DoD level 1, February 2026. Most of the time goes to LLM round-trips and rate limits.",
        color=TEXT_SECONDARY,
        fontsize=9,
        ha="left",
        va="top",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return OUT_PATH


def main() -> int:
    runs = load_runs()
    if not runs:
        print(f"❌  No runs with metadata found in {RUNS_DIR}")
        return 1
    out = generate_runs_chart(runs)
    print(f"✅  {out.relative_to(ROOT)} ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
