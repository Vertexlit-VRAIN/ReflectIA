# registry.py

from typing import Callable, Dict, Any, Iterable, Mapping
from .core_metrics import (
    num_turns,
    num_student_messages,
    num_ai_messages,
    avg_tokens_student,
    avg_tokens_ai,
    num_ai_questions,
    exploration_ratio_ai,
)

Message = Mapping[str, Any]

METRIC_REGISTRY: Dict[str, Callable[[Iterable[Message]], float]] = {
    "num_turns": num_turns,
    "num_student_messages": num_student_messages,
    "num_ai_messages": num_ai_messages,
    "avg_tokens_student": avg_tokens_student,
    "avg_tokens_ai": avg_tokens_ai,

    # NEW:
    "num_ai_questions": num_ai_questions,
    "exploration_ratio_ai": exploration_ratio_ai,
}
