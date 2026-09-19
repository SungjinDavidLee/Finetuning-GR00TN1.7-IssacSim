#!/usr/bin/env python3
"""Generate the figures in assets/ from data/task_summary.csv.

    python3 scripts/plot.py

Only matplotlib and the standard library are required. Labels are English so
the figures render the same on machines without a Korean font.
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "assets")

INK, MUT, GRID = "#1b1f24", "#6b7480", "#e3e7ec"
BLUE, TEAL, AMBER, RED, GREY = "#2f6feb", "#1f9d8f", "#d99000", "#cf3b3b", "#9aa4b1"

# open-loop replay: our displacement over the reference, per axis, at PSCALE 0.012
AXIS_RATIO = {"x": 1.14, "y": 1.01, "z": 1.81}

# end-effector tracking error with the policy switched off (mm), centre line
CONTROL = [(0.45, 1.41), (0.55, 2.08), (0.62, 2.80),
           (0.68, 3.76), (0.74, 5.35), (0.80, 8.97)]


def load():
    with open(os.path.join(DATA, "task_summary.csv"), newline="") as fp:
        return list(csv.DictReader(fp))


def style(ax, title=None, xlabel=None, ylabel=None, grid="y"):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=9, length=0)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=13, fontweight="bold",
                     loc="left", pad=14)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUT, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUT, fontsize=10)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), dpi=170, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote assets/" + name)


def fig_compare(rows):
    x = [int(r["task"]) for r in rows]
    fr5 = [100 * int(r["placed"]) / int(r["n"]) for r in rows]
    frk = [100 * int(r["franka_placed"]) / int(r["franka_n"]) for r in rows]
    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    ax.bar([i - 0.19 for i in x], frk, width=0.36, color=BLUE,
           label="Franka Panda (7-DoF)")
    ax.bar([i + 0.19 for i in x], fr5, width=0.36, color=TEAL,
           label="FR5 + AG-95 (6-DoF)")
    ax.set_xticks(x)
    ax.set_xticklabels(["T%d" % i for i in x])
    ax.set_ylim(0, 110)
    style(ax, "Placement success per task — same policy, same scene, same criterion",
          ylabel="success rate (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="upper center",
              ncol=2, bbox_to_anchor=(0.5, 1.0))
    ax.annotate("6-DoF cannot reach\ninto the drawer", xy=(4.19, 4),
                xytext=(2.6, 30), fontsize=8.5, color=RED, ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))
    ax.annotate("longest transport\n(241 mm)", xy=(6.19, 8),
                xytext=(7.9, 30), fontsize=8.5, color=AMBER, ha="center",
                arrowprops=dict(arrowstyle="->", color=AMBER, lw=1))
    save(fig, "task-compare.png")


def fig_funnel(rows):
    n = sum(int(r["n"]) for r in rows)
    stages = [("Episodes", n),
              ("Grasp attempted", sum(int(r["grasp_attempt"]) for r in rows)),
              ("Object lifted", sum(int(r["lifted"]) for r in rows)),
              ("Placed on the plate", sum(int(r["placed"]) for r in rows))]
    colors = [GREY, BLUE, TEAL, AMBER]
    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    y = list(range(len(stages)))[::-1]
    ax.barh(y, [v for _, v in stages], color=colors, height=0.6)
    for yi, (_, v) in zip(y, stages):
        ax.text(v + 6, yi, "%d  (%.1f%%)" % (v, 100 * v / n), va="center",
                color=INK, fontsize=10, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([s for s, _ in stages])
    ax.set_xlim(0, n * 1.25)
    style(ax, "Pipeline funnel — FR5, %d episodes" % n,
          xlabel="episodes passing the stage", grid="x")
    save(fig, "funnel.png")


def fig_axis_ratio():
    fig, axes = plt.subplots(1, 2, figsize=(14.6, 4.2))
    fig.subplots_adjust(wspace=0.28)

    ax = axes[0]
    ks = list(AXIS_RATIO)
    vs = [AXIS_RATIO[k] for k in ks]
    cols = [TEAL if abs(v - 1) < 0.2 else AMBER for v in vs]
    ax.bar(ks, vs, color=cols, width=0.5)
    ax.axhline(1.0, color=RED, linestyle="--", linewidth=1.4)
    for k, v in zip(ks, vs):
        ax.text(k, v + 0.04, "%.2f" % v, ha="center", fontsize=10, color=INK)
    ax.set_ylim(0, 2.1)
    style(ax, "Open-loop replay — displacement ratio at PSCALE 0.012",
          ylabel="FR5 / reference")
    ax.text(0.02, 0.93, "red line: matched", transform=ax.transAxes,
            fontsize=8.5, color=RED)

    ax = axes[1]
    ax.plot([c[0] for c in CONTROL], [c[1] for c in CONTROL], color=RED,
            linewidth=2.4, marker="o", markersize=6)
    ax.axvspan(0.80, 0.90, color=GREY, alpha=0.25)
    ax.text(0.845, 6.0, "IK failures\nwith lateral offset", ha="center",
            fontsize=9, color="#4b5563")
    ax.set_xlim(0.42, 0.90)
    style(ax, "Tracking error with the policy switched off",
          xlabel="distance from the robot base (m)",
          ylabel="commanded to achieved (mm)")
    save(fig, "calibration.png")


def main():
    rows = load()
    fig_compare(rows)
    fig_funnel(rows)
    fig_axis_ratio()


if __name__ == "__main__":
    main()
