#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IEEE-ready violin + boxplot + points for avg_tokens_student:
- violin (density)
- boxplot (median + IQR)
- jittered points (bounded, centered)
- NO mean, NO CI
- saves PDF (vector) + PNG (900 DPI)

Usage:
  python violin_box_student_tokens_ieee.py --raw raw.csv --outdir out
  python violin_box_student_tokens_ieee.py --raw raw.csv --outdir out --doublecol
"""

from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_violin_box_student_tokens(
    df: pd.DataFrame,
    out_pdf: Path,
    out_png: Path,
    dpi_png: int = 900,
    seed: int = 7,
    double_column: bool = False,
):
    # IEEE compact typography
    plt.rcParams.update({
        "font.size": 8,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    })

    rng = np.random.default_rng(seed)
    order = sorted(df["practice_id"].dropna().astype(str).unique().tolist())

    palette = ["C0", "C1", "C2", "C3"]
    color_by_group = {g: palette[i % len(palette)] for i, g in enumerate(order)}

    data = []
    n_by_group = {}

    for g in order:
        vals = pd.to_numeric(
            df.loc[df["practice_id"].astype(str) == g, "avg_tokens_student"],
            errors="coerce"
        ).dropna().to_numpy()
        data.append(vals)
        n_by_group[g] = int(vals.size)

    figsize = (7.0, 2.8) if double_column else (3.5, 2.8)
    fig, ax = plt.subplots(figsize=figsize)
    positions = np.arange(1, len(order) + 1)

    # --- Violin (light, background) ---
    vp = ax.violinplot(
        data,
        positions=positions,
        widths=0.9,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )
    for body in vp["bodies"]:
        body.set_alpha(0.25)
        body.set_edgecolor("none")

    # --- Boxplot (foreground, thin lines) ---
    ax.boxplot(
        data,
        positions=positions,
        widths=0.30,
        showfliers=False,
        medianprops={"linewidth": 1.3},
        whiskerprops={"linewidth": 1.0},
        capprops={"linewidth": 1.0},
        boxprops={"linewidth": 1.0},
    )

    # --- Points (bounded jitter, centered) ---
    jitter_width = 0.0
    for i, (g, vals) in enumerate(zip(order, data), start=1):
        if vals.size == 0:
            continue
        jitter = rng.uniform(-jitter_width, jitter_width, size=vals.size)
        ax.scatter(
            i + jitter,
            vals,
            s=16,
            alpha=0.65,
            color=color_by_group[g],
            edgecolors="none",
            zorder=3,
        )

    # X ticks with n
    ax.set_xticks(positions)
    ax.set_xticklabels([f"Project {g}\n(n={n_by_group[g]})" for g in order])

    # Axis label
    ax.set_ylabel("Message length")

    # Grid + spines
    ax.grid(True, axis="y", alpha=0.20)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)

    # Space for newline in x labels
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout()

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")              # vector
    fig.savefig(out_png, dpi=dpi_png, bbox_inches="tight") # raster
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="CSV raw con practice_id y avg_tokens_student")
    ap.add_argument("--outdir", default="out", help="Directorio de salida")
    ap.add_argument("--doublecol", action="store_true", help="Formato doble columna IEEE")
    args = ap.parse_args()

    df = pd.read_csv(args.raw)
    required = {"practice_id", "avg_tokens_student"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Faltan columnas en raw.csv: {sorted(missing)}")

    outdir = Path(args.outdir)
    plot_violin_box_student_tokens(
        df=df,
        out_pdf=outdir / "fig_student_tokens_violin_box_ieee.pdf",
        out_png=outdir / "fig_student_tokens_violin_box_ieee.png",
        double_column=args.doublecol,
    )

    print("OK ->", outdir / "fig_student_tokens_violin_box_ieee.pdf")
    print("OK ->", outdir / "fig_student_tokens_violin_box_ieee.png (900 DPI)")


if __name__ == "__main__":
    main()
