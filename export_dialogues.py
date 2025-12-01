"""
export_txt_dialogues.py

Exporta conversaciones limpias a ficheros .txt en formato:

# Dialogue A01 (practice=A, student=01)

[STUDENT]
texto...

[AI]
texto...

Cada fichero se guarda como output/A01.txt, B02.txt, etc.
"""

import json
from pathlib import Path
import argparse


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def parse_ids(folder_name: str):
    """
    Dado 'A01' devuelve:
      practice='A', student='01', conversation='A01'
    """
    if not folder_name:
        return "", "", ""
    return folder_name[0], folder_name[1:], folder_name


def load_messages(messages_path: Path):
    """Carga messages.json con formato lista o dict{'messages':...}."""
    content = json.loads(messages_path.read_text(encoding="utf-8"))
    if isinstance(content, list):
        return content
    if isinstance(content, dict) and "messages" in content:
        return content["messages"]
    raise ValueError(f"Formato inesperado en {messages_path}")


def is_conversation_message(msg: dict) -> bool:
    """Filtrado estándar."""
    return bool(msg.get("visible")) and bool(msg.get("conversation"))


def get_text(msg: dict) -> str:
    """Extrae texto desde msg['parts']."""
    parts = msg.get("parts", [])
    if isinstance(parts, list):
        return " ".join(str(p) for p in parts)
    return str(parts)


def role_to_label(role: str) -> str:
    """Convierte user/model a STUDENT/AI."""
    if role == "user":
        return "STUDENT"
    if role == "model":
        return "AI"
    return role.upper()


# -----------------------------------------------------------
# Export logic
# -----------------------------------------------------------

def export_conversation(conv_dir: Path, output_root: Path):
    """
    Exporta un solo directorio tipo A01 a A01.txt.
    """
    practice, student, convo_id = parse_ids(conv_dir.name)

    messages_path = conv_dir / "messages.json"
    if not messages_path.exists():
        print(f"[WARN] No messages.json en {conv_dir}")
        return False

    try:
        messages = load_messages(messages_path)
    except Exception as e:
        print(f"[WARN] Error cargando {messages_path}: {e}")
        return False

    # Filtrar solo los mensajes de conversación reales
    messages = [m for m in messages if is_conversation_message(m)]
    if not messages:
        print(f"[INFO] {convo_id}: sin mensajes de conversación")
        return False

    output_root.mkdir(parents=True, exist_ok=True)
    output_file = output_root / f"{convo_id}.txt"

    lines = []
    lines.append(f"# Dialogue {convo_id} (practice={practice}, student={student})\n")

    for msg in messages:
        label = role_to_label(msg.get("role", ""))
        text = get_text(msg).strip()

        lines.append(f"[{label}]")
        lines.append(text)
        lines.append("")  # línea en blanco

    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Exportado: {output_file}")
    return True


# -----------------------------------------------------------
# Main
# -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Exporta conversaciones a .txt sencillo")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output-root", type=Path, default=Path("dialogues"))

    args = parser.parse_args()

    if not args.data_root.exists():
        print(f"[ERROR] No existe carpeta: {args.data_root}")
        return

    count = 0
    for folder in sorted(args.data_root.iterdir()):
        if folder.is_dir():
            if export_conversation(folder, args.output_root):
                count += 1

    print(f"\nTotal diálogos exportados: {count}")


if __name__ == "__main__":
    main()
