"""
Centralized persistence for CritiCat.

Single per-student folder layout:

user_data/<user_id>/
  messages.json
  state.json
  files/
"""

import json
import os
from typing import Optional, Dict, Any, List

BASE_DIR = "data"


def _user_dir(user_id: str) -> str:
    return os.path.join(BASE_DIR, user_id)


def _ensure_user_dirs(user_id: str) -> None:
    os.makedirs(_user_dir(user_id), exist_ok=True)
    os.makedirs(get_user_files_dir(user_id), exist_ok=True)


def get_user_files_dir(user_id: str) -> str:
    """Directory where we persist uploaded files for the user."""
    return os.path.join(_user_dir(user_id), "files")


# -------------------- Chat History --------------------


def load_history(user_id: str) -> Optional[List[Dict[str, Any]]]:
    if not user_id:
        return None
    path = os.path.join(_user_dir(user_id), "messages.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_history(user_id: str, history: List[Dict[str, Any]]) -> None:
    if not user_id or history is None:
        return
    _ensure_user_dirs(user_id)
    path = os.path.join(_user_dir(user_id), "messages.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# -------------------- Config / Analysis State --------------------


def load_state(user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    path = os.path.join(_user_dir(user_id), "state.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalize
        data.setdefault("classification", None)
        data.setdefault("description", "")
        data.setdefault("files", [])
        data.setdefault("analysis", None)
        return data
    except Exception:
        return None


def save_state(user_id: str, state_obj: Dict[str, Any]) -> None:
    if not user_id or state_obj is None:
        return
    _ensure_user_dirs(user_id)
    path = os.path.join(_user_dir(user_id), "state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state_obj, f, indent=2, ensure_ascii=False)


# -------------------- Convenience lookups --------------------
def get_last_message_with_flag(user_id: str, flag: str) -> Optional[Dict[str, Any]]:
    hist = load_history(user_id) or []
    for m in reversed(hist):
        if m.get(flag):
            return m
    return None


def extract_text_from_parts(message: Dict[str, Any]) -> str:
    parts = message.get("parts") or []
    texts = [p for p in parts if isinstance(p, str)]
    return "\n\n".join(texts).strip() if texts else ""
