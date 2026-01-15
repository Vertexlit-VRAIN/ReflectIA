from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURATION
# ============================================================
INPUT_CSV = Path("metrics_output/feedback.csv")   # <-- adjust if needed
OUT_DIR = Path("figures") / "feedback_type"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_INSIDE_PCT = 3.0  # % threshold to place label inside the bar

# Colorblind-safe palette (Okabe–Ito inspired)
TYPE_COLORS = {
    "affective": "#0072B2",     # blue
    "directive": "#E69F00",     # orange
    "elaborative": "#D55E00",   # vermillion
    "evaluative": "#009E73",    # green
    "metacognitive": "#CC79A7", # purple
    "reinforcing": "#56B4E9",   # light blue
}

# ============================================================
# HELPERS
# ============================================================
def infer_group_from_filename(source_file: str) -> str:
    """
    Infers group from filenames like A05.txt, B01.md, etc.
    """
    stem = Path(str(source_file)).stem.strip().upper()
    if stem.startswith("A"):
        return "A"
    if stem.startswith("B"):
        return "B"
    return "UNKNOWN"

# ============================================================
# MAIN
# ============================================================
def main():
    df = pd.read_csv(INPUT_CSV)

    # --- Normalize feedback type ---
    df["type"] = df["type"].astype(str).str.strip().str.lower()

    # --- Ensure group column exists ---
    if "group" not in df.columns:
        df["group"] = df["source_file"].map(infer_group_from_filename)
    else:
        df["group"] = df["group"].astype(str).str.strip()
        missing = df["group"].isna() | (df["group"] == "") | (df["group"].str.lower() == "nan")
        if missing.any():
            df.loc[missing, "group"] = df.loc[missing, "source_file"].map(infer_group_from_filename)

    # Global list of feedback types (consistent order/colors)
    all_types = sorted(df["type"].unique())

    # --- One figure per group ---
    for grp in sorted(df["group"].dropna().unique()):
        sub = df[df["group"] == grp]
        if sub.empty:
            continue

        n = len(sub)

        counts = sub["type"].value_counts().reindex(all_types, fill_value=0)
        perc = (counts / counts.sum()) * 100

        fig = plt.figure(figsize=(max(6, 0.9 * len(all_types)), 5))
        ax = fig.add_subplot(111)

        colors = [TYPE_COLORS.get(t, "#999999") for t in perc.index]

        bars = ax.bar(
            perc.index,
            perc.values,
            color=colors,
            edgecolor="black",
            linewidth=0.6
        )

        # --- Percentage labels (inside or outside depending on size) ---
        for bar, value in zip(bars, perc.values):
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()

            if value >= MIN_INSIDE_PCT:
                # Inside bar
                ax.text(
                    x,
                    y * 0.95,
                    f"{value:.1f}%",
                    ha="center",
                    va="top",
                    color="white",
                    fontsize=10,
                    fontweight="bold"
                )
            else:
                # Outside bar (above)
                ax.text(
                    x,
                    y + 0.8,
                    f"{value:.1f}%",
                    ha="center",
                    va="bottom",
                    color="black",
                    fontsize=9
                )

        ax.set_title(f"Feedback type distribution - Project {grp} (n={n})")
        ax.set_xlabel("Feedback type")
        ax.set_ylabel("Percentage (%)")

        ax.tick_params(axis="x", rotation=45)
        plt.setp(ax.get_xticklabels(), ha="right")

        plt.tight_layout()
        out = OUT_DIR / f"feedback_type_distribution_group_{grp}.png"
        plt.savefig(out, dpi=300)
        plt.close(fig)

    print("✅ Figures saved to:", OUT_DIR.resolve())

# ============================================================
if __name__ == "__main__":
    main()
