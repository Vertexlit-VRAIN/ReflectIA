# registry.py

from typing import Callable, Dict, Any, Iterable, Mapping
from .core_metrics import (
    lexical_diversity_mtld,
    num_turns,
    num_student_messages,
    num_ai_messages,
    avg_tokens_student,
    avg_tokens_ai,
    num_ai_questions,
    exploration_ratio_ai,
    semantic_divergence,

    readability_ifsz_student,
    technical_knowledge_student,
    specificity_depth_student,

    readability_ifsz_ai,
    technical_knowledge_ai,
    specificity_depth_ai,
)

Message = Mapping[str, Any]

METRIC_REGISTRY: Dict[str, Callable[[Iterable[Message]], float]] = {
    "num_turns": num_turns,
    "num_student_messages": num_student_messages,
    "num_ai_messages": num_ai_messages,
    "avg_tokens_student": avg_tokens_student,
    "avg_tokens_ai": avg_tokens_ai,

    # Exploration
    "num_ai_questions": num_ai_questions,
    "exploration_ratio_ai": exploration_ratio_ai,

    # Advanced
    "semantic_divergence": semantic_divergence,
    "lexical_diversity_mtld": lexical_diversity_mtld,

    # Readability and content
    "readability_ifsz_student": readability_ifsz_student,
    "technical_knowledge_student": technical_knowledge_student,
    "specificity_depth_student": specificity_depth_student,

    "readability_ifsz_ai": readability_ifsz_ai,
    "technical_knowledge_ai": technical_knowledge_ai,
    "specificity_depth_ai": specificity_depth_ai,
}
