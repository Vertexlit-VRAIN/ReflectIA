#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Dict, Any, List

from metrics.config import CONFIG
from metrics.registry import METRIC_REGISTRY
from metrics.stats_utils import compute_metric_stats_from_long_rows


# =====================================================================
# Helpers
# =====================================================================

def parse_ids(conversation_folder_name: str):
    """
    Given a folder name like "A01", return:
      practice_id = "A"
      student_id  = "01"
      conversation_id = "A01"
    """
    if not conversation_folder_name:
        return "", "", ""

    practice_id = conversation_folder_name[0]
    student_id = conversation_folder_name[1:]
    conversation_id = conversation_folder_name
    return practice_id, student_id, conversation_id


def load_messages(messages_path: Path) -> List[Dict[str, Any]]:
    """
    Load messages from messages.json.
    Supports:
      - a top-level list [ {...}, {...} ]
      - or {"messages": [ {...}, {...} ] }
    """
    with messages_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "messages" in data:
        return data["messages"]

    raise ValueError(f"Unexpected JSON structure in {messages_path}")


# =====================================================================
# Long-format metric computation
# =====================================================================

def compute_all_long_rows() -> List[Dict[str, Any]]:
    """
    Traverse all conversation folders and compute long-format metric rows.
    """

    data_root: Path = CONFIG["data_root"]
    enabled_flags: Dict[str, bool] = CONFIG["metrics_enabled"]

    # Which metrics to compute (based on config)
    active_metrics = {
        name: func
        for name, func in METRIC_REGISTRY.items()
        if enabled_flags.get(name, False)
    }

    if not active_metrics:
        raise RuntimeError("No metrics enabled in CONFIG['metrics_enabled'].")

    rows: List[Dict[str, Any]] = []

    for conv_dir in sorted(p for p in data_root.iterdir() if p.is_dir()):
        messages_json = conv_dir / "messages.json"
        if not messages_json.exists():
            continue

        try:
            messages = load_messages(messages_json)
        except Exception as e:
            print(f"[WARN] Skipping {conv_dir.name}: cannot load messages ({e})")
            continue

        practice_id, student_id, conversation_id = parse_ids(conv_dir.name)

        # Compute all enabled metrics for this conversation
        for metric_name, metric_fn in active_metrics.items():
            try:
                value = metric_fn(messages)
            except Exception as e:
                print(f"[WARN] Metric '{metric_name}' failed for {conv_dir.name}: {e}")
                continue

            rows.append({
                "student_id": student_id,
                "practice_id": practice_id,
                "conversation_id": conversation_id,
                "metric_name": metric_name,
                "metric_value": value,
            })

    return rows


# =====================================================================
# CSV Writers
# =====================================================================

def write_long_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    """Write long-format CSV."""
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "student_id", "practice_id", "conversation_id",
        "metric_name", "metric_value"
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_stats_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    """Write per-practice × metric summary statistics."""

    import csv

    stats_rows = compute_metric_stats_from_long_rows(rows)

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["practice_id", "metric_name", "n", "mean", "sd", "ci_low", "ci_high"]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stats_rows)


def write_wide_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    """
    Convert long-format rows into wide format (one row per conversation):
        student_id | practice_id | conversation_id | metric1 | metric2 | ...
    Useful for Excel tables.
    """
    import csv
    from collections import defaultdict

    metric_names = sorted({r["metric_name"] for r in rows})

    # Key: (student_id, practice_id, conversation_id)
    grouped = defaultdict(dict)

    for r in rows:
        key = (r["student_id"], r["practice_id"], r["conversation_id"])
        grouped[key][r["metric_name"]] = r["metric_value"]

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["student_id", "practice_id", "conversation_id"] + metric_names

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for (student_id, practice_id, conversation_id), metric_dict in grouped.items():
            row = {
                "student_id": student_id,
                "practice_id": practice_id,
                "conversation_id": conversation_id
            }
            for m in metric_names:
                row[m] = metric_dict.get(m, "")
            writer.writerow(row)


# =====================================================================
# Main
# =====================================================================

def main():
    outputs = CONFIG["outputs"]

    long_csv = outputs["metrics_long_csv"]
    stats_csv = outputs["metrics_stats_csv"]
    wide_csv = outputs["metrics_wide_csv"]

    rows = compute_all_long_rows()

    write_long_csv(rows, long_csv)
    print(f"✅ Wrote long-format metrics → {long_csv}")

    write_stats_csv(rows, stats_csv)
    print(f"✅ Wrote per-practice statistics → {stats_csv}")

    write_wide_csv(rows, wide_csv)
    print(f"✅ Wrote wide-format conversation metrics → {wide_csv}")


if __name__ == "__main__":
    main()
