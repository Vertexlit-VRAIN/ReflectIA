"""
Utilities for handling and processing images.
"""

import base64
from functools import lru_cache


# Cache for base64 encoded images to avoid re-processing
@lru_cache(maxsize=50)
def cached_encode_image_to_base64(image_path, file_size):
    """Convert image to base64 string with caching"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        return None


def encode_image_to_base64(image_path):
    """Convert image to base64 string for Ollama with caching"""
    try:
        import os

        file_size = os.path.getsize(image_path)

        # Try cached version first
        cached_result = cached_encode_image_to_base64(image_path, file_size)
        if cached_result:
            return cached_result

        # Fallback to direct encoding if cache fails
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return {
            "error": f"❌ **Error**: No s'ha trobat el fitxer d'imatge: {image_path}"
        }
    except PermissionError:
        return {"error": f"❌ **Error**: No es tenen permisos per llegir: {image_path}"}
    except Exception as e:
        return {"error": f"❌ **Error**: No s'ha pogut processar la imatge: {str(e)}"}
