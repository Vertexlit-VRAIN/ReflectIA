from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_violin_minimal(
    df: pd.DataFrame,
    out_pdf: Path,
    out_png: Path,
    dpi_png: int = 600,
    double_column: bool = False,
    bw_method: float = 0.4,
):
    # Compact typography for IEEE
    plt.rcParams.update({
        "font.size": 8,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    })

    order = sorted(df["practice_id"].dropna().astype(str).unique().tolist())

    # Data and n per group
    data = []
    n_by_group = {}
    for g in order:
        vals = pd.to_numeric(
            df.loc[df["practice_id"].astype(str) == g, "num_turns"],
            errors="coerce"
        ).dropna().to_numpy()
        data.append(vals)
        n_by_group[g] = int(vals.size)

    figsize = (7.0, 2.8) if double_column else (3.5, 2.8)
    fig, ax = plt.subplots(figsize=figsize)
    positions = np.arange(1, len(order) + 1)

    # --- Violin (grayscale, outlined, print-friendly) ---
    vp = ax.violinplot(
        data,
        positions=positions,
        widths=0.9,
        showmeans=False,
        showmedians=False,
        showextrema=False,
        bw_method=bw_method,
    )
    for body in vp["bodies"]:
        body.set_facecolor("0.6")
        body.set_alpha(0.20)
        body.set_edgecolor("0.35")
        body.set_linewidth(0.8)

    # --- Boxplot (black lines, white fill) ---
    bp = ax.boxplot(
        data,
        positions=positions,
        widths=0.25,
        showfliers=False,
        patch_artist=True,
        medianprops={"linewidth": 1.3, "color": "0.0"},
        whiskerprops={"linewidth": 1.1, "color": "0.0"},
        capprops={"linewidth": 1.1, "color": "0.0"},
        boxprops={"linewidth": 1.1, "color": "0.0"},
    )
    for box in bp["boxes"]:
        box.set_facecolor("1.0")
        box.set_alpha(1.0)

    # X ticks with n
    xticklabels = [f"Project {g}\n(n={n_by_group[g]})" for g in order]
    ax.set_xticks(positions)
    ax.set_xticklabels(xticklabels)

    ax.set_ylabel("Turns per dialogue")

    # Grid: light major y-grid only
    ax.grid(True, axis="y", which="major", alpha=0.15, linewidth=0.8)
    ax.set_axisbelow(True)

    # Spines: reduce clutter
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)

    # Space for newline in x tick labels
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout()

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")              # vector
    fig.savefig(out_png, dpi=dpi_png, bbox_inches="tight") # raster
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="CSV raw con practice_id y num_turns")
    ap.add_argument("--outdir", default="out", help="Directorio de salida")
    ap.add_argument("--dpi", type=int, default=900, help="DPI para PNG")
    ap.add_argument("--bw", type=float, default=0.4, help="Bandwidth KDE del violín")
    ap.add_argument("--doublecol", action="store_true", help="Formato doble columna (~7in ancho)")
    args = ap.parse_args()

    df = pd.read_csv(args.raw)
    needed = {"practice_id", "num_turns"}
    missing = needed - set(df.columns)
    if missing:
        raise SystemExit(f"Faltan columnas en raw.csv: {sorted(missing)}")

    outdir = Path(args.outdir)
    plot_violin_minimal(
        df=df,
        out_pdf=outdir / "fig_turns_violin_ieee_minimal.pdf",
        out_png=outdir / "fig_turns_violin_ieee_minimal.png",
        dpi_png=args.dpi,
        double_column=args.doublecol,
        bw_method=args.bw,
    )

    print("OK ->", outdir / "fig_turns_violin_ieee_minimal.pdf")
    print(f"OK -> {outdir / 'fig_turns_violin_ieee_minimal.png'} (dpi={args.dpi})")


if __name__ == "__main__":
    main()
