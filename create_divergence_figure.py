#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Semantic displacement between student prompts and AI responses
(conversation centroids, paper-ready) + summary tables.

Outputs:
  figures/semantic_divergence/
    - semantic_displacement_practice_A.png
    - semantic_displacement_practice_B.png
    - summary_by_practice.csv
    - summary_by_conversation.csv

Usage:
  python semantic_displacement_centroids.py --data-root data --dpi 900 --thr 0.25 0.35 0.60
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import patheffects as pe

from metrics.helpers import (
    default_is_conversation_msg,
    get_message_text,
    get_embedding_model,
    cosine_distance,
)

Message = Mapping[str, Any]
METRIC_NAME = "semantic_divergence"


# ---------------------------------------------------------------------
# IO + IDs
# ---------------------------------------------------------------------
def load_messages(messages_path: Path) -> List[Dict[str, Any]]:
    with messages_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "messages" in data:
        return data["messages"]
    raise ValueError(f"Unexpected JSON structure in {messages_path}")


def parse_ids(folder_name: str) -> Tuple[str, str, str]:
    practice_id = folder_name[0]
    student_id = folder_name[1:]
    return practice_id, student_id, folder_name


# ---------------------------------------------------------------------
# Turn-level pairs
# ---------------------------------------------------------------------
def extract_pairs(messages: Iterable[Message]) -> List[Dict[str, Any]]:
    msgs = list(messages)
    user_txt, model_txt = [], []

    for i in range(len(msgs) - 1):
        a, b = msgs[i], msgs[i + 1]
        if not default_is_conversation_msg(a) or not default_is_conversation_msg(b):
            continue
        if a.get("role") == "user" and b.get("role") == "model":
            u = (get_message_text(a) or "").strip()
            m = (get_message_text(b) or "").strip()
            if u and m:
                user_txt.append(u)
                model_txt.append(m)

    if not user_txt:
        return []

    model = get_embedding_model()
    Eu = model.encode(user_txt)
    Em = model.encode(model_txt)

    pairs = []
    for vu, vm in zip(Eu, Em):
        pairs.append(
            dict(
                emb_user=np.asarray(vu, dtype=np.float32),
                emb_model=np.asarray(vm, dtype=np.float32),
                dist=float(cosine_distance(vu, vm)),
            )
        )
    return pairs


# ---------------------------------------------------------------------
# Aggregation per conversation + thresholds
# ---------------------------------------------------------------------
def summarize_turn_distances(d: np.ndarray, thresholds: List[float]) -> Dict[str, Any]:
    """
    d: distances per turn pair (cosine distance)
    thresholds: e.g. [0.25, 0.35, 0.60]
    returns mean/median/p90 and % below/above thresholds
    """
    if d.size == 0:
        return dict(
            n_pairs=0,
            mean=np.nan,
            median=np.nan,
            p90=np.nan,
            **{f"pct_le_{t:.2f}": np.nan for t in thresholds},
            pct_ge_0_60=np.nan,
        )

    out = {
        "n_pairs": int(d.size),
        "mean": float(d.mean()),
        "median": float(np.median(d)),
        "p90": float(np.percentile(d, 90)),
    }

    for t in thresholds:
        out[f"pct_le_{t:.2f}"] = float(np.mean(d <= t) * 100.0)

    # commonly used "high reframing" threshold (if 0.60 is included)
    out["pct_ge_0_60"] = float(np.mean(d >= 0.60) * 100.0)

    return out


def summarize_conversation(pairs: List[Dict[str, Any]], thresholds: List[float]) -> Dict[str, Any]:
    Eu = np.vstack([p["emb_user"] for p in pairs])
    Em = np.vstack([p["emb_model"] for p in pairs])
    d = np.array([p["dist"] for p in pairs], dtype=np.float64)

    stats = summarize_turn_distances(d, thresholds)

    return dict(
        centroid_user=Eu.mean(axis=0),
        centroid_model=Em.mean(axis=0),
        avg_dist=stats["mean"],
        p90_dist=stats["p90"],
        dists=d,
        **stats,
    )


# ---------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------
def project_umap(E: np.ndarray) -> np.ndarray:
    try:
        import umap  # type: ignore
    except ImportError:
        from sklearn.decomposition import PCA
        return PCA(n_components=2).fit_transform(E)

    reducer = umap.UMAP(
        n_neighbors=15,
        min_dist=0.05,
        metric="cosine",
        random_state=0,
    )
    return reducer.fit_transform(E)


# ---------------------------------------------------------------------
# Plot (paper-ready)
# ---------------------------------------------------------------------
def plot_practice(rows: List[Dict[str, Any]], practice_id: str) -> plt.Figure:
    U = np.vstack([r["centroid_user"] for r in rows])
    M = np.vstack([r["centroid_model"] for r in rows])
    X = project_umap(np.vstack([U, M]))
    Xu, Xm = X[: len(rows)], X[len(rows) :]

    avg = np.array([r["avg_dist"] for r in rows], dtype=np.float64)
    p90 = np.array([r["p90_dist"] for r in rows], dtype=np.float64)

    # Normalize for sizing
    p90_min, p90_max = float(np.min(p90)), float(np.max(p90))
    p90_n = (p90 - p90_min) / (p90_max - p90_min + 1e-12)
    size = 35 + 50 * p90_n

    # Outliers by avg distance
    outlier_thr = np.percentile(avg, 85)

    # Typography / sizing
    mpl.rcParams.update({
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
    })

    fig, ax = plt.subplots(figsize=(7.2, 5.4))

    # Minimal spines + subtle grid (paper-ish)
    ax.grid(True, alpha=0.18, linewidth=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_title(f"Semantic displacement - Project {practice_id}", pad=8)

    # Color encodes avg distance (with colorbar)
    avg_min, avg_max = float(np.min(avg)), float(np.max(avg))
    cmap = plt.get_cmap("viridis")
    norm = mpl.colors.Normalize(vmin=avg_min, vmax=avg_max)

    # Markers: distinguish roles by shape + fill (avoid extra colors)
    student_face = "#FFFFFF"
    student_edge = "#333333"
    ai_face = "#333333"
    ai_edge = "#333333"

    # Centroids
    ax.scatter(
        Xu[:, 0], Xu[:, 1],
        s=size,
        facecolors=student_face,
        edgecolors=student_edge,
        linewidths=1.0,
        label="Student centroid",
        zorder=3,
    )
    ax.scatter(
        Xm[:, 0], Xm[:, 1],
        s=size,
        marker="s",
        facecolors=ai_face,
        edgecolors=ai_edge,
        linewidths=0.8,
        label="AI centroid",
        zorder=3,
    )

    # Arrows: colored by avg distance for interpretability
    for r, u, m, a in zip(rows, Xu, Xm, avg):
        color = cmap(norm(a))
        ax.annotate(
            "",
            xy=(m[0], m[1]),
            xytext=(u[0], u[1]),
            arrowprops=dict(
                arrowstyle="-|>",
                mutation_scale=12,   # flecha un poco más visible
                lw=1.6,              # línea más gruesa
                color=color,
                alpha=0.6,
                shrinkA=0,
                shrinkB=0,
            ),
            zorder=2,
        )

        # Label only outliers, with a white outline for readability
        if r["avg_dist"] >= outlier_thr:
            txt = ax.text(u[0], u[1], r["conversation_id"], fontsize=8, color="#111111", zorder=4)
            txt.set_path_effects([pe.withStroke(linewidth=3, foreground="white", alpha=0.9)])

    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")

    # Colorbar (avg distance)
    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("Avg cosine distance (student→AI)", rotation=90)

    # Legend
    ax.legend(frameon=False, loc="upper right")

    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------
# CSV Writers
# ---------------------------------------------------------------------
def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--dpi", type=int, default=900)
    ap.add_argument(
        "--thr",
        nargs="+",
        type=float,
        default=[0.25, 0.35, 0.60],
        help="Thresholds for reporting percent aligned (<= thr). Example: --thr 0.25 0.35 0.60",
    )
    args = ap.parse_args()

    thresholds = list(args.thr)

    outdir = Path("figures") / METRIC_NAME
    outdir.mkdir(parents=True, exist_ok=True)

    practice_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    conversation_table_rows: List[Dict[str, Any]] = []

    # Collect
    for conv in sorted(Path(args.data_root).iterdir()):
        if not conv.is_dir():
            continue

        msg_path = conv / "messages.json"
        if not msg_path.exists():
            continue

        practice_id, student_id, conv_id = parse_ids(conv.name)

        try:
            messages = load_messages(msg_path)
        except Exception:
            continue

        pairs = extract_pairs(messages)
        if not pairs:
            continue

        summ = summarize_conversation(pairs, thresholds)

        # store for plotting
        practice_rows[practice_id].append(
            dict(
                conversation_id=conv_id,
                practice_id=practice_id,
                student_id=student_id,
                centroid_user=summ["centroid_user"],
                centroid_model=summ["centroid_model"],
                avg_dist=summ["avg_dist"],
                p90_dist=summ["p90_dist"],
            )
        )

        # store for conversation-level table
        row = {
            "practice_id": practice_id,
            "student_id": student_id,
            "conversation_id": conv_id,
            "n_pairs": summ["n_pairs"],
            "mean_div": round(summ["mean"], 6),
            "median_div": round(summ["median"], 6),
            "p90_div": round(summ["p90"], 6),
            "pct_ge_0_60": round(summ["pct_ge_0_60"], 2),
        }
        for t in thresholds:
            row[f"pct_le_{t:.2f}"] = round(summ[f"pct_le_{t:.2f}"], 2)
        conversation_table_rows.append(row)

    # Generate figures per practice + practice-level table
    practice_table_rows: List[Dict[str, Any]] = []

    for practice_id, rows in sorted(practice_rows.items()):
        if not rows:
            continue

        # Save figure
        fig = plot_practice(rows, practice_id)
        outpath = outdir / f"semantic_displacement_practice_{practice_id}.png"
        fig.savefig(outpath, dpi=args.dpi)
        plt.close(fig)
        print(f"✅ Saved {outpath}")

        # Practice-level aggregation computed from conversation table rows
        conv_rows_this = [r for r in conversation_table_rows if r["practice_id"] == practice_id]
        all_means = np.array([float(r["mean_div"]) for r in conv_rows_this], dtype=np.float64)
        all_medians = np.array([float(r["median_div"]) for r in conv_rows_this], dtype=np.float64)
        all_p90 = np.array([float(r["p90_div"]) for r in conv_rows_this], dtype=np.float64)

        p_row = {
            "practice_id": practice_id,
            "conversations": len(rows),
            "pairs_total": int(sum(r["n_pairs"] for r in conversation_table_rows if r["practice_id"] == practice_id)),
            "mean_div_conversations": round(float(all_means.mean()), 6) if len(all_means) else "",
            "median_div_conversations": round(float(np.median(all_medians)), 6) if len(all_medians) else "",
            "p90_div_conversations": round(float(np.median(all_p90)), 6) if len(all_p90) else "",
        }

        # mean of percentages across conversations
        for t in thresholds:
            vals = [float(r[f"pct_le_{t:.2f}"]) for r in conv_rows_this]
            p_row[f"pct_le_{t:.2f}_avg"] = round(float(np.mean(vals)), 2) if vals else ""
        vals_hi = [float(r["pct_ge_0_60"]) for r in conv_rows_this]
        p_row["pct_ge_0_60_avg"] = round(float(np.mean(vals_hi)), 2) if vals_hi else ""

        practice_table_rows.append(p_row)

    # Write tables
    conv_fields = (
        ["practice_id", "student_id", "conversation_id", "n_pairs", "mean_div", "median_div", "p90_div"]
        + [f"pct_le_{t:.2f}" for t in thresholds]
        + ["pct_ge_0_60"]
    )
    write_csv(outdir / "summary_by_conversation.csv", conv_fields, conversation_table_rows)

    prac_fields = (
        ["practice_id", "conversations", "pairs_total", "mean_div_conversations",
         "median_div_conversations", "p90_div_conversations"]
        + [f"pct_le_{t:.2f}_avg" for t in thresholds]
        + ["pct_ge_0_60_avg"]
    )
    write_csv(outdir / "summary_by_practice.csv", prac_fields, practice_table_rows)

    print(f"\nTables written to: {outdir.resolve()}")


if __name__ == "__main__":
    main()
