from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIG ---
INPUT_CSV = Path("metrics_output/quality.csv")   # <-- cambia el nombre si hace falta
OUT_DIR = Path("figures") / "quality"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def normalize_order(values, preferred):
    # mantiene preferred y añade otros al final si aparecen
    seen = set(preferred)
    rest = [v for v in values if v not in seen]
    return preferred + rest

def main():
    df = pd.read_csv(INPUT_CSV)

    MAP_DEPTH = {
        "MEDIUM": "MED",
        "MED": "MED",
        "LOW": "LOW",
        "HIGH": "HIGH",
    }

    df["attr_depth"] = (
        df["attr_depth"].astype(str).str.strip().str.upper().map(MAP_DEPTH).fillna(df["attr_depth"])
    )
    df["attr_relevance"] = (
        df["attr_relevance"].astype(str).str.strip().str.upper().map(MAP_DEPTH).fillna(df["attr_relevance"])
    )



    # Limpieza mínima
    for col in ["attr_concreteness", "attr_depth", "attr_relevance"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    # Orden sugerido (ajústalo si tus categorías cambian)
    concreteness_order = normalize_order(sorted(df["attr_concreteness"].unique()), ["ABSTRACT", "CONCRETE"])
    depth_order        = normalize_order(sorted(df["attr_depth"].unique()),        ["LOW", "MED", "HIGH"])
    relevance_order    = normalize_order(sorted(df["attr_relevance"].unique()),    ["LOW", "MED", "HIGH"])

    # ==========================================================
    # 1) HEATMAP por concreteness (depth x relevance)
    # ==========================================================
    # Preparamos una figura con 1 panel por concreteness
    n_panels = len(concreteness_order)
    fig = plt.figure(figsize=(6 * n_panels, 5))

    for i, conc in enumerate(concreteness_order, start=1):
        ax = fig.add_subplot(1, n_panels, i)

        sub = df[df["attr_concreteness"] == conc]

        # tabla depth (filas) x relevance (cols)
        heat = pd.crosstab(sub["attr_depth"], sub["attr_relevance"]).reindex(
            index=depth_order, columns=relevance_order, fill_value=0
        )

        im = ax.imshow(heat.values)  # sin fijar colores a mano

        ax.set_title(f"Concreteness: {conc}")
        ax.set_xlabel("attr_relevance")
        ax.set_ylabel("attr_depth")

        ax.set_xticks(np.arange(len(heat.columns)))
        ax.set_xticklabels(heat.columns)

        ax.set_yticks(np.arange(len(heat.index)))
        ax.set_yticklabels(heat.index)

        # anotaciones (conteos)
        for r in range(heat.shape[0]):
            for c in range(heat.shape[1]):
                ax.text(c, r, str(heat.iat[r, c]), ha="center", va="center")

    plt.tight_layout()
    out1 = OUT_DIR / "heatmap_quality_por_concreteness.png"
    plt.savefig(out1, dpi=300)
    plt.close(fig)

    # ==========================================================
    # 2) BARRAS: por concreteness, distribución de depth (apilado por relevance)
    # ==========================================================
    # Construimos tabla: (concreteness, depth) x relevance
    tab = (
        df.groupby(["attr_concreteness", "attr_depth", "attr_relevance"])
          .size()
          .unstack("attr_relevance", fill_value=0)
    )

    # reindex orden
    tab = tab.reindex(
        pd.MultiIndex.from_product([concreteness_order, depth_order], names=["attr_concreteness", "attr_depth"]),
        fill_value=0
    )
    tab = tab.reindex(columns=relevance_order, fill_value=0)

    fig2 = plt.figure(figsize=(10, 6))
    ax2 = fig2.add_subplot(111)

    # ploteo apilado: un bloque por concreteness (con 3 depth dentro)
    # índice a etiquetas tipo "CONCRETE | MED"
    x_labels = [f"{idx[0]} | {idx[1]}" for idx in tab.index]
    bottom = np.zeros(len(tab))

    for rel in tab.columns:
        vals = tab[rel].values
        ax2.bar(x_labels, vals, bottom=bottom, label=rel)
        bottom += vals

    ax2.set_title("Quality: Depth (x) con Relevance apilada, separado por Concreteness")
    ax2.set_xlabel("attr_concreteness | attr_depth")
    ax2.set_ylabel("Nº de ejemplos")
    ax2.tick_params(axis="x", rotation=45)
    plt.setp(ax2.get_xticklabels(), ha="right")
    ax2.legend(title="attr_relevance")

    plt.tight_layout()
    out2 = OUT_DIR / "barras_apiladas_depth_relevance_por_concreteness.png"
    plt.savefig(out2, dpi=300)
    plt.close(fig2)

    print("✅ Figuras guardadas en:", OUT_DIR.resolve())
    print(" -", out1.resolve())
    print(" -", out2.resolve())

if __name__ == "__main__":
    main()
