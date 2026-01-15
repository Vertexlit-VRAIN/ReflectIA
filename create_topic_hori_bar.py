from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# --- CONFIG ---
INPUT_CSV = Path("metrics_output/topic.csv")  # <-- change if needed
OUT_DIR = Path("figures") / "thematic_codes"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOP_N = 12                 # show top N codes (per group)
ADD_OTHER = True           # include an "OTHER" bar for the remaining codes
MIN_PCT_TO_LABEL = 1.0     # if a bar is tiny, place label outside (readability)

def infer_group_from_filename(source_file: str) -> str:
    stem = Path(str(source_file)).stem.strip().upper()
    if stem.startswith("A"):
        return "A"
    if stem.startswith("B"):
        return "B"
    return "UNKNOWN"

def main():
    df = pd.read_csv(INPUT_CSV)

    # --- Normalize columns ---
    df["attr_code"] = df["attr_code"].astype(str).str.strip().str.upper()

    # Ensure group exists (infer if missing)
    if "group" not in df.columns:
        df["group"] = df["source_file"].map(infer_group_from_filename)
    else:
        df["group"] = df["group"].astype(str).str.strip()
        missing = df["group"].isna() | (df["group"] == "") | (df["group"].str.lower() == "nan")
        if missing.any():
            df.loc[missing, "group"] = df.loc[missing, "source_file"].map(infer_group_from_filename)

    # --- Global, consistent color map: code -> color (same across all groups) ---
    all_codes = sorted(df["attr_code"].unique().tolist())

    # Use a large categorical palette; if many codes, sample evenly from a continuous map.
    # 'tab20' has 20 distinct colors; for more, we sample from 'turbo' (still consistent).
    if len(all_codes) <= 20:
        palette = list(cm.get_cmap("tab20").colors)
        code_to_color = {code: palette[i] for i, code in enumerate(all_codes)}
    else:
        cmap = cm.get_cmap("turbo")
        code_to_color = {code: cmap(i / (len(all_codes) - 1)) for i, code in enumerate(all_codes)}

    # --- One figure per group ---
    for grp in sorted(df["group"].dropna().unique()):
        sub = df[df["group"] == grp]
        if sub.empty:
            continue

        n = len(sub)

        counts = sub["attr_code"].value_counts()
        perc = (counts / counts.sum()) * 100

        # Top N (+ OTHER)
        top = perc.head(TOP_N).copy()
        if ADD_OTHER and len(perc) > TOP_N:
            other_val = perc.iloc[TOP_N:].sum()
            top.loc["OTHER"] = other_val

        # For plotting: smallest at bottom -> biggest on top (nice in horizontal bars)
        top = top.sort_values(ascending=True)

        labels = top.index.tolist()
        values = top.values.tolist()

        # Colors: consistent mapping for codes; "OTHER" in light gray
        colors = [
            code_to_color.get(code, (0.5, 0.5, 0.5, 1.0)) if code != "OTHER" else (0.75, 0.75, 0.75, 1.0)
            for code in labels
        ]

        fig = plt.figure(figsize=(8, max(4.5, 0.45 * len(labels))))
        ax = fig.add_subplot(111)

        bars = ax.barh(labels, values, color=colors, edgecolor="black", linewidth=0.6)

        # % labels: inside near the right end; if tiny bar, put outside
        for bar, value in zip(bars, values):
            y = bar.get_y() + bar.get_height() / 2
            x = bar.get_width()

            if value >= MIN_PCT_TO_LABEL:
                ax.text(
                    x * 0.98, y, f"{value:.1f}%",
                    ha="right", va="center",
                    color="white", fontsize=9, fontweight="bold"
                )
            else:
                ax.text(
                    x + 0.3, y, f"{value:.1f}%",
                    ha="left", va="center",
                    color="black", fontsize=9
                )

        ax.set_title(f"Thematic code distribution - Project {grp} (n={n})")
        ax.set_xlabel("Percentage (%)")
        ax.set_ylabel("Code")

        # Give a bit of headroom on the x-axis
        xmax = max(values) if values else 1
        ax.set_xlim(0, xmax * 1.15)

        plt.tight_layout()
        out = OUT_DIR / f"thematic_code_distribution_group_{grp}.png"
        plt.savefig(out, dpi=300)
        plt.close(fig)

    print("✅ Figures saved to:", OUT_DIR.resolve())

if __name__ == "__main__":
    main()
