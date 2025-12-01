# config.py
"""
Central configuration for metrics computation.
You can toggle metrics here and change paths without touching the logic.
"""

from pathlib import Path

CONFIG = {
    "data_root": Path("data"),
    "outputs": {
        "metrics_long_csv": Path("metrics_output/metrics_raw.csv"),
        "metrics_stats_csv": Path("metrics_output/metrics_stats.csv"),
        "metrics_wide_csv": Path("metrics_output/metrics_wide.csv"),
    },
    "metrics_enabled": {
        "num_turns": True,
        "num_student_messages": True,
        "num_ai_messages": True,
        "avg_tokens_student": True,
        "avg_tokens_ai": True,

        # NEW exploration metrics
        "num_ai_questions": True,
        "exploration_ratio_ai": True,
    },
}
