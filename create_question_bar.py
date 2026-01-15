
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIG ---
INPUT_CSV = Path("metrics_output/question.csv")  # change if needed
OUT_DIR = Path("figures") / "question_subtype"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OKABE_ITO = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
]

def infer_group_from_filename(source_file: str) -> str:
    stem = Path(str(source_file)).stem.strip().upper()
    if stem.startswith("A"):
        return "A"
    if stem.startswith("B"):
        return "B"
    return "UNKNOWN"

def main():
    df = pd.read_csv(INPUT_CSV)

    # --- Normalization ---
    df["attr_subtype"] = df["attr_subtype"].astype(str).str.strip().str.lower()

    # Ensure group column exists
    if "group" not in df.columns:
        df["group"] = df["source_file"].map(infer_group_from_filename)
    else:
        df["group"] = df["group"].astype(str).str.strip()
        missing = df["group"].isna() | (df["group"] == "") | (df["group"].str.lower() == "nan")
        if missing.any():
            df.loc[missing, "group"] = df.loc[missing, "source_file"].map(infer_group_from_filename)

    # Optional: unify subtype variants
    subtype_map = {
        "organisation": "organizational",
        "organization": "organizational",
        "organizational": "organizational",
        "explore": "exploratory",
        "exploratory": "exploratory",
        "clarificatory": "clarificatory",
        "procedural": "procedural",
        "reflective": "reflective",
    }
    df["attr_subtype"] = df["attr_subtype"].map(lambda x: subtype_map.get(x, x))

    # Global subtype list (consistent color mapping across groups)
    all_subtypes = sorted(df["attr_subtype"].unique())

    # Map subtype -> color (stable). If more subtypes than palette, cycle (still consistent).
    subtype_to_color = {
        st: OKABE_ITO[i % len(OKABE_ITO)]
        for i, st in enumerate(all_subtypes)
    }

    # --- One figure per group ---
    for grp in sorted(df["group"].dropna().unique()):
        sub = df[df["group"] == grp]
        if sub.empty:
            continue

        n = len(sub)

        counts = sub["attr_subtype"].value_counts()
        perc = (counts / counts.sum()) * 100
        perc = perc.sort_values(ascending=False)

        fig = plt.figure(figsize=(max(6, 0.9 * len(perc)), 5))
        ax = fig.add_subplot(111)

        colors = [subtype_to_color[st] for st in perc.index]

        bars = ax.bar(
            perc.index,
            perc.values,
            color=colors,
            edgecolor="black",
            linewidth=0.6
        )

        # Percentage labels INSIDE the bars (top-inside)
        for bar, value in zip(bars, perc.values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 0.95,
                f"{value:.1f}%",
                ha="center",
                va="top",
                color="white",
                fontsize=10,
                fontweight="bold"
            )

        ax.set_title(f"Question subtype distribution — Group {grp} (n={n})")
        ax.set_xlabel("Question subtype")
        ax.set_ylabel("Percentage (%)")

        ax.tick_params(axis="x", rotation=45)
        plt.setp(ax.get_xticklabels(), ha="right")

        plt.tight_layout()
        out = OUT_DIR / f"question_subtype_distribution_group_{grp}.png"
        plt.savefig(out, dpi=300)
        plt.close(fig)

    print("✅ Figures saved to:", OUT_DIR.resolve())

if __name__ == "__main__":
    main()

