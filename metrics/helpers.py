"""
Helper functions for filtering and working with message dictionaries.
"""

import math
import re
import string
import numpy as np

_EMBEDDING_MODEL = None
_NLP_MODEL = None

def get_embedding_model():
    """
    Lazy loads a multilingual SentenceTransformer model.
    Uses 'paraphrase-multilingual-MiniLM-L12-v2' which is 
    excellent for Catalan semantic similarity and very fast.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            # This downloads the model once (~400MB)
            _EMBEDDING_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except ImportError:
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
    return _EMBEDDING_MODEL

def get_nlp_model():
    """
    Lazy loader for Spacy Catalan model.
    Required for sentence segmentation in IFSZ calculation.
    """
    global _NLP_MODEL
    if _NLP_MODEL is None:
        try:
            import spacy
            # Ensure you have run: python -m spacy download ca_core_news_sm
            
            # Disable heavy components we don't need for readability (parser, ner)
            # This makes it much faster and uses way less memory.
            _NLP_MODEL = spacy.load("ca_core_news_sm", exclude=["parser", "ner"])
            
            # Add a sentence segmenter since we disabled the parser
            if "sentencizer" not in _NLP_MODEL.pipe_names:
                _NLP_MODEL.add_pipe("sentencizer")

            # Increase limit to handle massive text blobs (e.g. 5 million chars)
            _NLP_MODEL.max_length = 5_000_000
            
        except OSError:
            raise ImportError(
                "Spacy Catalan model not found. Please run: "
                "python -m spacy download ca_core_news_sm"
            )
        except ImportError:
             raise ImportError("Spacy not installed. Run: pip install spacy")
    return _NLP_MODEL

def count_syllables_ca(word: str) -> int:
    """
    Approximate syllable count using vowel groups for Catalan.
    Used for Flesch-Szigriszt.
    """
    word = word.lower()
    # Matches sequences of vowels (including accents/dieresis)
    return len(re.findall(r'[aeiouàèéíòóúüïü]+', word))

def cosine_distance(vec_a, vec_b) -> float:
    """
    Computes Cosine Distance (1 - Cosine Similarity).
    Range: 0 (identical) to 2 (opposite).
    """
    # Normalize vectors
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 1.0  # Max divergence if one vector is empty

    dot_product = np.dot(vec_a, vec_b)
    similarity = dot_product / (norm_a * norm_b)

    # Clip to avoid numerical errors going slightly beyond -1 or 1
    similarity = np.clip(similarity, -1.0, 1.0)

    return 1.0 - similarity

def clean_and_tokenize(text: str) -> list:
    """
    Removes punctuation and splits into tokens for lexicon matching.
    """
    if not text:
        return []
    # Replace punctuation with spaces to avoid concatenating words
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    clean_text = text.lower().translate(translator)
    return clean_text.split()

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
