"""
Client for interacting with different AI providers.
"""

import base64
import io
import requests
import google.generativeai as genai
from PIL import Image

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_MODEL,
    OLLAMA_URL,
    TIMEOUT_SECONDS,
)


def call_ai_model(provider, prompt, images_base64=None):
    """Call the specified AI model provider."""
    if provider == "ollama":
        return call_ollama_model(prompt, images_base64)
    elif provider == "gemini":
        return call_gemini_model(prompt, images_base64)
    else:
        return f"❌ **Error**: Proveïdor d'IA no reconegut: {provider}"


def call_gemini_model(prompt, images_base64=None):
    """Call the Gemini API.

    Args:
        prompt (str): The text prompt for the model.
        images_base64 (list, optional): A list of base64 encoded images.

    Returns:
        str: The response from the model or an error message.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return """❌ **Error**: No s'ha trobat la clau de l'API de Gemini.

🔧 **Solució**: Assegureu-vos que heu configurat la variable d'entorn `GEMINI_API_KEY` al fitxer `.env`. """

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        content = [prompt]
        if images_base64:
            for img_b64 in images_base64:
                try:
                    img_data = base64.b64decode(img_b64)
                    img = Image.open(io.BytesIO(img_data))
                    content.append(img)
                except Exception as e:
                    return f"❌ **Error**: No s'ha pogut processar una imatge per a Gemini. Error: {e}"

        response = model.generate_content(content)
        return response.text

    except Exception as e:
        return f"❌ **Error Inesperat amb Gemini**: {e}"


def call_ollama_model(prompt, images_base64=None):
    """Call local Ollama model"""
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}

        # Add images if provided
        if images_base64:
            payload["images"] = images_base64

        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)

        if response.status_code == 200:
            result = response.json()
            return result.get(
                "response", "❌ **Error**: No s'ha rebut resposta del model"
            )
        else:
            return f"❌ **Error del Model**: Ollama ha retornat l'estat {response.status_code}\n\n🔧 **Solució**: Comproveu que el model '{OLLAMA_MODEL}' està instal·lat i disponible."

    except requests.exceptions.ConnectionError:
        return """❌ **Error de Connexió**: No s'ha pogut connectar amb Ollama

🔧 **Solucions possibles**:
- Assegureu-vos que Ollama està instal·lat i funcionant
- Executeu `ollama serve` al terminal
- Comproveu que el servei funciona a http://localhost:11434"""
    except requests.exceptions.Timeout:
        return """⏱️ **Error de Temps d'Espera**: El model ha trigat massa temps a respondre

🔧 **Solucions possibles**:
- Reduïu el nombre d'imatges
- Comproveu la connexió de xarxa
- Reinicieu el servei Ollama"""
    except Exception as e:
        return f"❌ **Error Inesperat**: {str(e)}\n\n🔧 **Solució**: Comproveu la configuració del sistema i torneu-ho a intentar."