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
        # Basic
        "num_turns": True,
        "num_student_messages": True,
        "num_ai_messages": True,
        "avg_tokens_student": True,
        "avg_tokens_ai": True,

        # Exploration
        "num_ai_questions": True,
        "exploration_ratio_ai": True,

        # Advanced
        "semantic_divergence": True,
        "lexical_diversity_mtld": True,

        # Content and readability
        "readability_ifsz_student": True,
        "technical_knowledge_student": True,
        "specificity_depth_student": True,
        
        # AI Content
        "readability_ifsz_ai": True,
        "technical_knowledge_ai": True,
        "specificity_depth_ai": True,
    },
}
