from typing import Iterable, Mapping, Callable, Any
from .helpers import (
    default_is_conversation_msg,
    get_message_text,
    count_tokens,
    round_value,
    is_question_message_ca,
)

Message = Mapping[str, Any]


def num_turns(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> int:
    return sum(1 for m in messages if is_conv_msg(m))


def num_student_messages(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> int:
    return sum(
        1 for m in messages
        if is_conv_msg(m) and m.get("role") == "user"
    )


def num_ai_messages(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> int:
    return sum(
        1 for m in messages
        if is_conv_msg(m) and m.get("role") == "model"
    )


# ---------- Message length / duration ----------

def _avg_tokens_for_role(
    messages: Iterable[Message],
    role: str,
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    token_counts = []
    for m in messages:
        if not (is_conv_msg(m) and m.get("role") == role):
            continue
        text = get_message_text(m)
        token_counts.append(count_tokens(text))

    if not token_counts:
        return 0.0

    return sum(token_counts) / len(token_counts)


def avg_tokens_student(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return round_value(_avg_tokens_for_role(messages, role="user", is_conv_msg=is_conv_msg))


def avg_tokens_ai(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return round_value(_avg_tokens_for_role(messages, role="model", is_conv_msg=is_conv_msg))


# ---------- NEW: Exploration (questions vs answers) ----------

def num_ai_questions(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> int:
    """
    Number of AI turns (role == 'model') that are questions
    in Catalan, according to our heuristic.
    """
    count = 0
    for m in messages:
        if not (is_conv_msg(m) and m.get("role") == "model"):
            continue
        if is_question_message_ca(m):
            count += 1
    return count


def exploration_ratio_ai(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    """
    Exploration Ratio for AI:
        ( #AI turns that are questions / #AI turns ) * 100
    Returns a percentage (0–100) rounded to 2 decimals.
    """
    n_ai = num_ai_messages(messages, is_conv_msg=is_conv_msg)
    if n_ai == 0:
        return 0.0

    q_ai = num_ai_questions(messages, is_conv_msg=is_conv_msg)
    ratio = (q_ai / n_ai) * 100.0
    return round_value(ratio)
