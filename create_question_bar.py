from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIG ---
INPUT_CSV = Path("metrics_output/question.csv")  # original CSV
OUT_DIR = Path("figures") / "interaction_subtype"
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

def normalize_text(x) -> str:
    # robust normalization for subtype strings
    s = str(x) if x is not None else ""
    s = s.strip().lower()
    s = " ".join(s.split())  # collapse multiple whitespace
    return s

def main():
    df = pd.read_csv(INPUT_CSV)

    # --- Basic sanity checks ---
    required_cols = {"source_file", "attr_subtype"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"CSV is missing required columns: {missing_cols}. Found: {list(df.columns)}")

    # --- Normalization ---
    df["attr_subtype"] = df["attr_subtype"].map(normalize_text)

    # Ensure group column exists / is filled
    if "group" not in df.columns:
        df["group"] = df["source_file"].map(infer_group_from_filename)
    else:
        df["group"] = df["group"].astype(str).str.strip()
        missing = df["group"].isna() | (df["group"] == "") | (df["group"].str.lower() == "nan")
        if missing.any():
            df.loc[missing, "group"] = df.loc[missing, "source_file"].map(infer_group_from_filename)

    # --- Canonicalize original subtypes (including common variants/typos) ---
    canonical_map = {
        # organizational variants
        "organisation": "organizational",
        "organization": "organizational",
        "organizational": "organizational",
        "organisational": "organizational",
        "org": "organizational",

        # reflective variants
        "reflective": "reflective",
        "reflection": "reflective",
        "reflect": "reflective",

        # clarification variants
        "clarificatory": "clarificatory",
        "clarification": "clarificatory",
        "clarify": "clarificatory",

        # exploration variants
        "exploratory": "exploratory",
        "explore": "exploratory",
        "exploration": "exploratory",

        # procedural variants
        "procedural": "procedural",
        "procedure": "procedural",
        "howto": "procedural",
        "how-to": "procedural",
        "how to": "procedural",
    }
    df["attr_subtype"] = df["attr_subtype"].map(lambda x: canonical_map.get(x, x))

    # --- New display labels ---
    new_label_map = {
        "organizational": "Task-management",
        "reflective": "Critical-evaluation",
        "clarificatory": "Clarification",
        "exploratory": "Design-exploration",
        "procedural": "How-to implementation",
    }

    df["subtype_label"] = df["attr_subtype"].map(new_label_map).fillna("Other / unmapped")

    # --- Debug summary (helps you spot why bars were empty) ---
    print("\n=== DEBUG: raw attr_subtype value_counts (top 20) ===")
    print(df["attr_subtype"].value_counts().head(20))
    print("\n=== DEBUG: mapped subtype_label value_counts ===")
    print(df["subtype_label"].value_counts())

    # Fixed order (include Other at end if present)
    subtype_order = [
        "Task-management",
        "Critical-evaluation",
        "Clarification",
        "Design-exploration",
        "How-to implementation",
        "Other / unmapped",
    ]
    present = set(df["subtype_label"].unique())
    subtype_order = [s for s in subtype_order if s in present]

    # Stable color mapping
    subtype_to_color = {
        st: OKABE_ITO[i % len(OKABE_ITO)]
        for i, st in enumerate(subtype_order)
    }

    # --- One figure per group ---
    for grp in sorted(df["group"].dropna().unique()):
        sub = df[df["group"] == grp]
        if sub.empty:
            continue

        n = len(sub)

        counts = sub["subtype_label"].value_counts()
        perc = (counts / counts.sum()) * 100

        # IMPORTANT: keep a stable order and DO NOT drop missing -> fill with 0
        perc = perc.reindex(subtype_order, fill_value=0)
        perc = perc.sort_values(ascending=False)

        fig = plt.figure(figsize=(max(8, 0.9 * len(perc)), 5))
        ax = fig.add_subplot(111)

        colors = [subtype_to_color[st] for st in perc.index]

        bars = ax.bar(
            perc.index,
            perc.values,
            color=colors,
            edgecolor="black",
            linewidth=0.6
        )

        # Labels (only if bar > 0 to avoid weird placements)
        for bar, value in zip(bars, perc.values):
            if value <= 0:
                continue
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

        ax.set_title(f"Interaction subtype distribution - Project {grp} (n={n})")
        ax.set_xlabel("Interaction subtype")
        ax.set_ylabel("Percentage (%)")

        ax.tick_params(axis="x", rotation=25)
        plt.setp(ax.get_xticklabels(), ha="right")

        # give a bit of headroom
        ymax = max(1, perc.max() * 1.15)
        ax.set_ylim(0, ymax)

        plt.tight_layout()
        out = OUT_DIR / f"interaction_subtype_distribution_group_{grp}.png"
        plt.savefig(out, dpi=300)
        plt.close(fig)

    print("\n✅ Figures saved to:", OUT_DIR.resolve())

if __name__ == "__main__":
    main()
