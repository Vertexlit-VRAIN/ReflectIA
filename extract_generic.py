#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
import pandas as pd

# ---- helpers ----

ATTR_RE = re.compile(r'(\w+)\s*=\s*(".*?"|\'.*?\')', re.DOTALL)

def parse_attrs(attr_str: str) -> dict:
    """
    Parsea atributos estilo:  code="LAY" role='student'
    Devuelve dict {code: LAY, role: student}
    """
    attrs = {}
    for k, v in ATTR_RE.findall(attr_str):
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        attrs[k] = v
    return attrs

def infer_group(filename: str) -> str:
    name = Path(filename).stem.upper()
    if name.startswith("A"):
        return "A"
    if name.startswith("B"):
        return "B"
    return "UNKNOWN"

def build_tag_regex(label: str, mode: str) -> re.Pattern:
    """
    mode:
      - closed: <label ...> ... </label>
      - block : <label ...> ... (hasta next <label ...> o EOF o </label>)
    """
    safe = re.escape(label)
    if mode == "closed":
        # exige cierre </label>
        pattern = rf"(?is)<{safe}\b(?P<attrs>[^>]*)>(?P<text>.*?)</{safe}\s*>"
    elif mode == "block":
        # no exige cierre; corta en next <label ...>, o </label>, o EOF
        pattern = rf"(?is)<{safe}\b(?P<attrs>[^>]*)>(?P<text>.*?)(?=(</{safe}\s*>|<{safe}\b|$))"
    else:
        raise ValueError("mode debe ser 'closed' o 'block'")
    return re.compile(pattern)

# ---- main ----

def parse_args():
    p = argparse.ArgumentParser(
        description="Parser genérico: extrae <label ...>...</label> a CSV, sacando attrs automáticamente."
    )
    p.add_argument("label", help="Nombre del tag/label (ej: topic, feedback, question, quality)")
    p.add_argument("--mode", choices=["closed", "block"], default="closed",
                   help="closed=requiere </label>. block=corta en siguiente <label> o EOF aunque falte cierre.")
    p.add_argument("--input-dir", default=None,
                   help="Directorio de entrada. Default: metrics_output/<label>")
    p.add_argument("--output-csv", default=None,
                   help="CSV salida. Default: metrics_output/<label>_extraido.csv")
    p.add_argument("--ext", default=".txt,.md",
                   help="Extensiones separadas por coma. Default: .txt,.md")
    p.add_argument("--attrs", default=None,
                   help="Lista de attrs a extraer (coma-separated). Si se omite, extrae TODOS los attrs encontrados.")
    return p.parse_args()

def main():
    args = parse_args()
    label = args.label.strip()
    if not label:
        raise SystemExit("❌ label vacío.")

    input_dir = Path(args.input_dir) if args.input_dir else Path("metrics_output") / label
    output_csv = Path(args.output_csv) if args.output_csv else Path("metrics_output") / f"{label}_extraido.csv"
    exts = {e.strip().lower() for e in args.ext.split(",") if e.strip()}

    wanted_attrs = None
    if args.attrs:
        wanted_attrs = {a.strip() for a in args.attrs.split(",") if a.strip()}
        if not wanted_attrs:
            wanted_attrs = None

    if not input_dir.exists():
        raise SystemExit(f"❌ No existe el directorio de entrada: {input_dir.resolve()}")

    tag_re = build_tag_regex(label, mode=args.mode)

    all_rows = []
    all_attr_keys_seen = set()

    for file in input_dir.rglob("*"):
        if file.is_dir() or file.suffix.lower() not in exts:
            continue

        content = file.read_text(encoding="utf-8", errors="ignore")
        group = infer_group(file.name)

        for m in tag_re.finditer(content):
            attrs_str = m.group("attrs") or ""
            attrs = parse_attrs(attrs_str)

            if wanted_attrs is not None:
                attrs = {k: v for k, v in attrs.items() if k in wanted_attrs}

            # normaliza texto (sin romper idiomas)
            text = re.sub(r"\s+", " ", (m.group("text") or "").strip())

            row = {
                "label": label,
                "source_file": file.name,
                "group": group,
                "text": text,
            }

            # attrs -> columnas attr_<k>
            for k, v in attrs.items():
                row[f"attr_{k}"] = v
                all_attr_keys_seen.add(k)

            all_rows.append(row)

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise SystemExit(f"❌ No se encontró ningún <{label} ...> en {input_dir.resolve()} (mode={args.mode})")

    # Garantiza columnas para todos los attrs vistos (rellena NaN)
    for k in sorted(all_attr_keys_seen):
        col = f"attr_{k}"
        if col not in df.columns:
            df[col] = ""

    # Orden de columnas más amigable
    fixed_cols = ["label", "source_file", "group", "text"]
    attr_cols = sorted([c for c in df.columns if c.startswith("attr_")])
    other_cols = [c for c in df.columns if c not in fixed_cols + attr_cols]
    df = df[fixed_cols + attr_cols + other_cols]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"✅ CSV generado: {output_csv.resolve()} | Filas: {len(df)} | Attrs detectados: {len(all_attr_keys_seen)}")

if __name__ == "__main__":
    main()
