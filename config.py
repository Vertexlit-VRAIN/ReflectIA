"""
Configuration constants for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Ollama Configuration ---
AI_PROVIDER = "gemini"  # "ollama" or "gemini"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
TIMEOUT_SECONDS = 600

# --- Gemini Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-lite"


# --- UI Configuration ---
MAX_IMAGES = 10
