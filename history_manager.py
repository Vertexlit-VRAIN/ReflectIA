"""
Manages loading and saving of conversation history to JSON files.
"""
import json
import os

MESSAGES_DIR = "messages"

def load_history(user_id):
    """
    Loads the conversation history for a given user_id from a JSON file.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        list or None: A list representing the conversation history if the file
                      exists, otherwise None.
    """
    if not user_id:
        return None

    history_file = os.path.join(MESSAGES_DIR, f"{user_id}.json")

    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None  # Return None if file is corrupted or unreadable
    return None

def save_history(user_id, history):
    """
    Saves the conversation history for a given user_id to a JSON file.

    Args:
        user_id (str): The unique identifier for the user.
        history (list): The conversation history to save.
    """
    if not user_id or history is None:
        return

    # Ensure the messages directory exists
    if not os.path.exists(MESSAGES_DIR):
        os.makedirs(MESSAGES_DIR)

    history_file = os.path.join(MESSAGES_DIR, f"{user_id}.json")

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
