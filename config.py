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
MAX_IMAGES = 20

# --- Debugging ---
DEBUG_MODE = True
DEBUG_LLM_OUTPUT = """
## Anàlisi d'Imatges de Prova

Aquesta és una resposta de prova per a la depuració de la interfície.

### Imatge 1: portada.jpg

*   **Qualitat Visual**: Bona
*   **Adequació**: Correcta
*   **Recomanacions**:
    *   Millorar el contrast del títol.
    *   Utilitzar una imatge de més resolució.

### Imatge 2: interior.jpg

*   **Qualitat Visual**: Excel·lent
*   **Adequació**: Perfecta
*   **Recomanacions**:
    *   Cap recomanació. El disseny és excel·lent.
"""
