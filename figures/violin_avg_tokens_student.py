#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IEEE-ready violin + boxplot for avg_tokens_student:
- violin (density)
- boxplot (median + IQR)
- NO points
- NO mean, NO CI
- saves PNG only (900 DPI)

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
    out_png: Path,
    dpi_png: int = 900,
    double_column: bool = False,
):
    # IEEE compact typography
    plt.rcParams.update({
        "font.size": 8,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    })

    order = sorted(df["practice_id"].dropna().astype(str).unique().tolist())

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

    # X ticks with n
    ax.set_xticks(positions)
    ax.set_xticklabels([f"Project {g}\n(n={n_by_group[g]})" for g in order])

    # Axis label
    ax.set_ylabel("Message length (tokens)")

    # Grid + spines
    ax.grid(True, axis="y", alpha=0.20)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)

    # Space for newline in x labels
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=dpi_png, bbox_inches="tight")
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
        out_png=outdir / "fig_student_tokens_violin_box_ieee.png",
        double_column=args.doublecol,
    )

    print("OK ->", outdir / "fig_student_tokens_violin_box_ieee.png (900 DPI)")


if __name__ == "__main__":
    main()
