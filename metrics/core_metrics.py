from typing import Iterable, Mapping, Callable, Any, Set
from .helpers import (
    default_is_conversation_msg,
    clean_and_tokenize,
    get_message_text,
    count_tokens,
    round_value,
    is_question_message_ca,
    get_embedding_model,
    get_nlp_model,
    cosine_distance,
    count_syllables_ca,
)

from .lexicon_ca import TECHNICAL_TERMS_CA, SPECIFIC_TERMS_CA

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

# ----- Semantic and lexical -----

def semantic_divergence(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    """
    Calculates the average Semantic Divergence (Distance) between 
    a Student's message and the AI's immediate response.
    
    1.0 = Identical meaning (Low Divergence) -> This is Cosine Similarity
    We want DIVERGENCE, so we return 1 - Similarity.
    
    Result:
      0.0 = Perfectly aligned
      1.0 = Very different (High topic drift or misunderstanding)
    """
    model = get_embedding_model()
    
    student_vecs = []
    ai_vecs = []
    
    # Convert iterable to list for indexing
    msgs = list(messages)
    
    # Find pairs: User message -> followed immediately by AI message
    for i in range(len(msgs) - 1):
        curr_msg = msgs[i]
        next_msg = msgs[i+1]
        
        if not is_conv_msg(curr_msg) or not is_conv_msg(next_msg):
            continue
            
        if curr_msg.get("role") == "user" and next_msg.get("role") == "model":
            # Extract text
            txt_student = get_message_text(curr_msg).strip()
            txt_ai = get_message_text(next_msg).strip()
            
            if txt_student and txt_ai:
                # We collect them to batch encode (faster)
                student_vecs.append(txt_student)
                ai_vecs.append(txt_ai)

    if not student_vecs:
        return 0.0 # No pairs found
        
    # Batch encode
    embeddings_student = model.encode(student_vecs)
    embeddings_ai = model.encode(ai_vecs)
    
    distances = []
    for v_s, v_a in zip(embeddings_student, embeddings_ai):
        dist = cosine_distance(v_s, v_a)
        distances.append(dist)
        
    if not distances:
        return 0.0
        
    avg_dist = sum(distances) / len(distances)
    return round_value(avg_dist, 4)


def lexical_diversity_mtld(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    """
    Computes MTLD (Measure of Textual Lexical Diversity) for the AI's responses.
    MTLD is robust against text length differences (unlike TTR).
    
    Higher Value = Richer Vocabulary.
    """
    try:
        from lexical_diversity import lex_div as ld
    except ImportError:
        print("Install lexical_diversity: pip install lexical-diversity")
        return 0.0

    # 1. Aggregate all AI text
    ai_text_blobs = []
    for m in messages:
        if is_conv_msg(m) and m.get("role") == "model":
            text = get_message_text(m)
            if text:
                ai_text_blobs.append(text)
    
    full_text = " ".join(ai_text_blobs)
    
    if not full_text.strip():
        return 0.0

    # 2. Tokenize (Simple split is often enough, or use library's tokenizer)
    # The library expects a list of tokens
    tokens = ld.tokenize(full_text)
    
    if len(tokens) < 10:
        return 0.0 # Too short for valid LDI
        
    # 3. Compute MTLD
    val = ld.mtld(tokens)
    
    return round_value(val)

# ----------------

def _compute_readability_ifsz(
    messages: Iterable[Message],
    role: str,
    is_conv_msg: Callable[[Message], bool]
) -> float:
    """
    Helper to compute IFSZ for a specific role (user or model).
    """
    # 1. Aggregate Text
    text_blobs = []
    for m in messages:
        if is_conv_msg(m) and m.get("role") == role:
            text = get_message_text(m)
            if text:
                text_blobs.append(text)
    
    full_text = " ".join(text_blobs)
    if not full_text.strip():
        return 0.0
        
    # 2. NLP Processing
    nlp = get_nlp_model()
    doc = nlp(full_text)
    
    words = [token.text for token in doc if token.is_alpha]
    sentences = list(doc.sents)
    
    n_words = len(words)
    n_sentences = len(sentences)
    
    if n_words == 0 or n_sentences == 0:
        return 0.0

    # 3. Calculation
    n_syllables = sum(count_syllables_ca(w) for w in words)
    syllables_per_word = n_syllables / n_words
    words_per_sentence = n_words / n_sentences
    
    ifsz = 206.835 - (62.3 * syllables_per_word) - words_per_sentence
    return round_value(ifsz)


def readability_ifsz_student(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return _compute_readability_ifsz(messages, "user", is_conv_msg)


def readability_ifsz_ai(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return _compute_readability_ifsz(messages, "model", is_conv_msg)


# =====================================================================
# Domain Knowledge (Lexicons)
# =====================================================================

def _compute_lexicon_density(
    messages: Iterable[Message], 
    lexicon: Set[str], 
    role: str, 
    is_conv_msg
) -> float:
    """Helper: (Matching Terms / Total Tokens) * 100"""
    total_tokens = 0
    match_count = 0
    
    for m in messages:
        if is_conv_msg(m) and m.get("role") == role:
            text = get_message_text(m)
            tokens = clean_and_tokenize(text)
            
            total_tokens += len(tokens)
            for t in tokens:
                if t in lexicon:
                    match_count += 1
                    
    if total_tokens == 0:
        return 0.0
        
    return round_value((match_count / total_tokens) * 100.0)


# --- Student Metrics ---

def technical_knowledge_student(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return _compute_lexicon_density(messages, TECHNICAL_TERMS_CA, "user", is_conv_msg)


def specificity_depth_student(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return _compute_lexicon_density(messages, SPECIFIC_TERMS_CA, "user", is_conv_msg)


# --- AI Metrics ---

def technical_knowledge_ai(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return _compute_lexicon_density(messages, TECHNICAL_TERMS_CA, "model", is_conv_msg)


def specificity_depth_ai(
    messages: Iterable[Message],
    is_conv_msg: Callable[[Message], bool] = default_is_conversation_msg,
) -> float:
    return _compute_lexicon_density(messages, SPECIFIC_TERMS_CA, "model", is_conv_msg)
