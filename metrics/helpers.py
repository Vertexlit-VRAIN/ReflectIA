"""
Helper functions for filtering and working with message dictionaries.
"""

import math
import re


def default_is_conversation_msg(msg) -> bool:
    """
    Determine whether a message should be included in metrics.
    According to your rules:
        visible == True AND conversation == True
    """
    return bool(msg.get("visible")) and bool(msg.get("conversation"))


def get_message_text(msg) -> str:
    """
    Extract text from a message in a consistent way.
    Use this if metrics need text content (future metrics).
    """
    parts = msg.get("parts", [])
    if isinstance(parts, list):
        return " ".join(str(p) for p in parts)
    return str(parts)


def count_tokens(text: str) -> int:
    """
    Very simple token counter: splits on whitespace.
    Interprets 'tokens' as words here.
    """
    if not text:
        return 0
    return len(str(text).split())


def round_value(val, decimals: int = 2):
    """
    Safely round numeric values (floats or ints).
    Returns NaN unchanged.
    """
    try:
        if isinstance(val, float) and math.isnan(val):
            return val
        return round(val, decimals)
    except Exception:
        return val


# --------- Catalan question detection ---------

# Common Catalan interrogative words
INTERROGATIVE_TOKENS_CA = {
    "què", "que", "qui", "on", "quan", "com", "quant",
    "quants", "quantes", "quin", "quina", "quins", "quines",
}

# Multi-word interrogatives that often start a question
INTERROGATIVE_MULTIWORD_CA = {
    "per què", "perque", "per què no", "què et", "què en",
}

# Question-intent phrases (often 2nd person forms)
QUESTION_PHRASES_CA = {
    "pots", "podries", "podem", "vols", "voldries",
    "t'agradaria", "et sembla", "què et sembla",
    "em pots", "em podries", "em sabries dir",
    "creus que", "penses que", "diries que",
}


def is_question_like_ca(text: str) -> bool:
    """
    Heuristic detector for Catalan questions.

    Rules:
    - If there's a "?" anywhere → question.
    - Otherwise, look for interrogatives or question-intent verbs
      at the beginning of sentences.
    """
    if not text:
        return False

    t = text.strip().lower()

    # Fast path: explicit question mark
    if "?" in t:
        return True

    # Split in rough "sentences"
    sentences = re.split(r"[.!;:\n]+", t)

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        tokens = s.split()
        if not tokens:
            continue

        first = tokens[0]
        first_two = " ".join(tokens[:2])

        if first in INTERROGATIVE_TOKENS_CA:
            return True
        if first_two in INTERROGATIVE_MULTIWORD_CA:
            return True

        # Look for question-intent verb patterns near the start
        prefix = " ".join(tokens[:4])  # first few words are usually enough
        for pat in QUESTION_PHRASES_CA:
            if prefix.startswith(pat + " ") or prefix.startswith("que " + pat + " "):
                return True

    return False


def is_question_message_ca(msg) -> bool:
    """
    Decide if a message (any role) is a question in Catalan,
    using is_question_like_ca on its text.
    """
    return is_question_like_ca(get_message_text(msg))
