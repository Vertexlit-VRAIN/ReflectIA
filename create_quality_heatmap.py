from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# CONFIGURATION
# ============================================================
INPUT_CSV = Path("metrics_output/quality.csv")
OUT_DIR = Path("figures") / "quality"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# If your CSV uses group values like "A" and "B", these will appear as "Project A" / "Project B"
PROJECT_LABEL = {
    "A": "Project A",
    "B": "Project B",
}

# ============================================================
# HELPERS
# ============================================================
def normalize_order(values, preferred):
    """
    Keeps preferred order and appends any unseen values at the end.
    """
    seen = set(preferred)
    rest = [v for v in values if v not in seen]
    return preferred + rest


def project_name_from_group(group_value: str) -> str:
    g = str(group_value).strip().upper()
    return PROJECT_LABEL.get(g, f"Project {g}")


# ============================================================
# MAIN
# ============================================================
def main():
    df = pd.read_csv(INPUT_CSV)

    # --------------------------------------------------------
    # Normalize depth / relevance labels (fix MED vs MEDIUM, etc.)
    # --------------------------------------------------------
    MAP_LEVELS = {
        "LOW": "LOW",
        "MED": "MED",
        "MEDIUM": "MED",
        "HIGH": "HIGH",
    }

    df["attr_depth"] = (
        df["attr_depth"]
        .astype(str)
        .str.strip()
        .str.upper()
        .map(MAP_LEVELS)
        .fillna(df["attr_depth"])
    )

    df["attr_relevance"] = (
        df["attr_relevance"]
        .astype(str)
        .str.strip()
        .str.upper()
        .map(MAP_LEVELS)
        .fillna(df["attr_relevance"])
    )

    # --------------------------------------------------------
    # Basic cleaning
    # --------------------------------------------------------
    for col in ["attr_concreteness", "attr_depth", "attr_relevance"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    # Ensure group exists
    if "group" not in df.columns:
        raise ValueError("CSV must include a 'group' column (e.g., A/B) to generate Project A / Project B figures.")

    df["group"] = df["group"].astype(str).str.strip().str.upper()

    # --------------------------------------------------------
    # Preferred semantic order (paper-consistent)
    # --------------------------------------------------------
    concreteness_order = normalize_order(
        sorted(df["attr_concreteness"].unique()),
        ["ABSTRACT", "CONCRETE"],
    )

    depth_order = normalize_order(
        sorted(df["attr_depth"].unique()),
        ["LOW", "MED", "HIGH"],
    )

    relevance_order = normalize_order(
        sorted(df["attr_relevance"].unique()),
        ["LOW", "MED", "HIGH"],
    )

    # =========================================================
    # Generate TWO sets of figures: one per group (Project A / Project B)
    # =========================================================
    for g in sorted(df["group"].dropna().unique()):
        sub_df = df[df["group"] == g]
        if sub_df.empty:
            continue

        project_name = project_name_from_group(g)
        n = len(sub_df)

        # =====================================================
        # 1) HEATMAP — Depth × Relevance, split by Concreteness
        # =====================================================
        n_panels = len(concreteness_order)
        fig = plt.figure(figsize=(6 * n_panels, 5))

        for i, conc in enumerate(concreteness_order, start=1):
            ax = fig.add_subplot(1, n_panels, i)

            sub = sub_df[sub_df["attr_concreteness"] == conc]

            heat = pd.crosstab(
                sub["attr_depth"],
                sub["attr_relevance"],
            ).reindex(
                index=depth_order,
                columns=relevance_order,
                fill_value=0,
            )

            ax.imshow(heat.values)

            ax.set_title(f"Concreteness: {conc}")
            ax.set_xlabel("Relevance")
            ax.set_ylabel("Depth")

            ax.set_xticks(np.arange(len(heat.columns)))
            ax.set_xticklabels(heat.columns)

            ax.set_yticks(np.arange(len(heat.index)))
            ax.set_yticklabels(heat.index)

            for r in range(heat.shape[0]):
                for c in range(heat.shape[1]):
                    ax.text(
                        c, r,
                        str(heat.iat[r, c]),
                        ha="center",
                        va="center",
                        fontsize=9,
                    )

        fig.suptitle(f"Quality heatmap — {project_name} (n={n})", y=1.02, fontsize=12)
        plt.tight_layout()

        out1 = OUT_DIR / f"quality_heatmap_depth_x_relevance_by_concreteness_{project_name.replace(' ', '_')}.png"
        plt.savefig(out1, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # =====================================================
        # 2) STACKED BARS — Depth distribution stacked by Relevance
        # =====================================================
        tab = (
            sub_df.groupby(["attr_concreteness", "attr_depth", "attr_relevance"])
            .size()
            .unstack("attr_relevance", fill_value=0)
        )

        tab = tab.reindex(
            pd.MultiIndex.from_product(
                [concreteness_order, depth_order],
                names=["Concreteness", "Depth"],
            ),
            fill_value=0,
        )

        tab = tab.reindex(columns=relevance_order, fill_value=0)

        fig2 = plt.figure(figsize=(10, 6))
        ax2 = fig2.add_subplot(111)

        x_labels = [f"{idx[0]} | {idx[1]}" for idx in tab.index]
        bottom = np.zeros(len(tab))

        for rel in tab.columns:
            values = tab[rel].values
            ax2.bar(x_labels, values, bottom=bottom, label=rel)
            bottom += values

        ax2.set_title(f"Quality dimensions — {project_name} (n={n})")
        ax2.set_xlabel("Concreteness | Depth")
        ax2.set_ylabel("Number of instances")

        ax2.tick_params(axis="x", rotation=45)
        plt.setp(ax2.get_xticklabels(), ha="right")

        ax2.legend(title="Relevance")
        plt.tight_layout()

        out2 = OUT_DIR / f"quality_stacked_depth_by_relevance_and_concreteness_{project_name.replace(' ', '_')}.png"
        plt.savefig(out2, dpi=300, bbox_inches="tight")
        plt.close(fig2)

        print("✅ Saved figures for", project_name)
        print(" -", out1.resolve())
        print(" -", out2.resolve())


if __name__ == "__main__":
    main()
