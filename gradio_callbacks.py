"""
Callback functions for the Gradio interface.
"""

import gradio as gr

from config import AI_PROVIDER, MAX_IMAGES, DEBUG_MODE, DEBUG_LLM_OUTPUT
from image_utils import encode_image_to_base64
from ai_providers import call_ai_model

conversation_history = {}

def generate_llm_response(
    user_id,
    files,
    classification,
    user_description,
    *type_selections,
    progress=gr.Progress()
):
    if DEBUG_MODE:
        return DEBUG_LLM_OUTPUT

    progress(0, desc="Validant les dades d'entrada...")

    if files:
        files = [f for f in files if f is not None]
    if not files:
        return "❌ **Error**: Si us plau, pugeu almenys una imatge per a l'anàlisi."

    if not user_id:
        return "❌ **Error**: Si us plau, introduïu el vostre identificador d'estudiant."

    if not classification:
        return "❌ **Error**: Si us plau, seleccioneu primer una classificació."

    valid_files = []
    valid_types = []
    for i, file in enumerate(files):
        if type_selections[i] is not None and type_selections[i] != "":
            valid_files.append(file)
            valid_types.append(type_selections[i])

    if not valid_files:
        return "❌ **Error**: Si us plau, especifiqueu el tipus per a almenys una imatge."

    progress(0.2, desc="Processant les imatges...")

    # Prepare images for Ollama
    images_base64 = []
    image_info = []

    for i, file in enumerate(valid_files):
        progress(
            0.2 + (0.3 * i / len(valid_files)),
            desc=f"Codificant imatge {i + 1} de {len(valid_files)}...",
        )
        if hasattr(file, "name"):
            image_path = file.name
        else:
            image_path = str(file)

        # Encode image to base64
        base64_result = encode_image_to_base64(image_path)
        if isinstance(base64_result, dict) and "error" in base64_result:
            return base64_result["error"]
        elif base64_result:
            images_base64.append(base64_result)
            filename = (
                image_path.split("/")[-1] if "/" in image_path else f"Image {i + 1}"
            )
            image_info.append(f"{filename} - {valid_types[i]}")
        else:
            return f"❌ **Error**: No s'ha pogut processar la imatge {i + 1}"

    # Create prompt for Ollama
    context = f"Classificació: {classification}"
    if user_description and user_description.strip():
        context += f"\nDescripció de l'usuari: {user_description.strip()}"

    context += f"\nImatges a analitzar: {', '.join(image_info)}"

    prompt = f"""
{context}

Analitza aquestes imatges segons la classificació '{classification}' i proporciona una anàlisi detallada en català.

Per a cada imatge, proporciona:
- Una avaluació de la qualitat visual
- Adequació per al tipus especificat ({', '.join(set(valid_types))})
- Recomanacions específiques

Respon amb punts clars i concisos.
"""

    progress(0.6, desc="Enviant petició al model d'IA...")

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    history = conversation_history[user_id]

    # Call AI model
    result = call_ai_model(AI_PROVIDER, prompt, images_base64, history)

    history.append({"role": "user", "parts": [prompt]})
    history.append({"role": "model", "parts": [result]})

    progress(1.0, desc="Anàlisi completada!")

    # Return simple result
    return format_analysis_results(result, classification, files, image_info)


def update_type_dropdowns(files, classification):
    if files:
        files = [f for f in files if f is not None]
    image_count = len(files) if files else 0
    counter_text = f"**Imatges**: {image_count}/{MAX_IMAGES}"

    if not classification:
        # Return updates for counter, rows, images and dropdowns
        return (
            [counter_text]
            + [gr.update(visible=False)] * MAX_IMAGES
            + [gr.update(visible=False, value=None)] * MAX_IMAGES
            + [gr.update(visible=False, choices=[], value=None)] * MAX_IMAGES
        )

    type_options = []
    if classification == "Editorial":
        type_options = ["portada", "interior"]
    elif classification == "Social Network":
        type_options = [
            "Instagram Artista",
            "Instagram Concurs",
            "Twitter Artista",
            "Twitter Concurs",
            "Newsletter",
            "Logo",
            "Capçalera",
        ]

    row_updates = []
    image_updates = []
    dropdown_updates = []

    if files:
        for i in range(len(files)):
            # Show row
            row_updates.append(gr.update(visible=True))
            # Show thumbnail image
            image_updates.append(gr.update(visible=True, value=files[i]))
            # Show dropdown with options and auto-detected value
            filename = files[i].name if hasattr(files[i], "name") else f"Image {i + 1}"
            if "/" in filename:
                filename = filename.split("/")[-1]  # Get just the filename from path

            # Auto-detect type based on filename
            auto_type = auto_detect_image_type(filename, classification)

            dropdown_updates.append(
                gr.update(
                    visible=True,
                    choices=type_options,
                    value=auto_type if auto_type in type_options else None,
                    label=f"Tipus per a {filename} {'(auto-detectat)' if auto_type else ''}",
                )
            )

        # Hide unused components
        for i in range(len(files), MAX_IMAGES):
            row_updates.append(gr.update(visible=False))
            image_updates.append(gr.update(visible=False, value=None))
            dropdown_updates.append(gr.update(visible=False, choices=[], value=None))
    else:
        row_updates = [gr.update(visible=False)] * MAX_IMAGES
        image_updates = [gr.update(visible=False, value=None)] * MAX_IMAGES
        dropdown_updates = [
            gr.update(visible=False, choices=[], value=None)
        ] * MAX_IMAGES

    return [counter_text] + row_updates + image_updates + dropdown_updates

def auto_detect_image_type(filename, classification):
    """Auto-detect image type based on filename and classification"""
    if not classification:
        return None

    filename_lower = filename.lower()

    if classification == "Editorial":
        if any(word in filename_lower for word in ["cover", "portada", "front"]):
            return "portada"
        elif any(word in filename_lower for word in ["inside", "interior", "page"]):
            return "interior"
        return "portada"  # Default to cover

    elif classification == "Social Network":
        if "instagram" in filename_lower:
            if any(
                word in filename_lower for word in ["contest", "concurs", "giveaway"]
            ):
                return "Instagram Concurs"
            return "Instagram Artista"
        elif "twitter" in filename_lower:
            if any(
                word in filename_lower for word in ["contest", "concurs", "giveaway"]
            ):
                return "Twitter Concurs"
            return "Twitter Artista"
        elif any(word in filename_lower for word in ["newsletter", "butlletí"]):
            return "Newsletter"
        elif any(word in filename_lower for word in ["logo", "logotip"]):
            return "Logo"
        elif any(
            word in filename_lower for word in ["header", "capçalera", "capcelera"]
        ):
            return "Capçalera"
        return "Instagram Artista"  # Default to Instagram artist

    return None

def update_button_and_status(user_id, files, classification, user_description, *type_selections):
    """Combined function to update both button state and status message"""
    # Common validation logic
    if files:
        files = [f for f in files if f is not None]
    if not files:
        return (
            gr.update(interactive=False),
            "📸 **Estat**: Pugeu una o més imatges per analitzar",
        )

    if not user_id:
        return (
            gr.update(interactive=False),
            "🧑‍🎓 **Estat**: Introduïu el vostre identificador d'estudiant per començar",
        )

    if not classification:
        return (
            gr.update(interactive=False),
            "📋 **Estat**: Seleccioneu primer una classificació (Editorial o Social Network)",
        )

    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]

    if not valid_types:
        return (
            gr.update(interactive=False),
            f"🏷️ **Estat**: Especifiqueu el tipus per a almenys una de les imatges",
        )

    if not user_description or not user_description.strip():
        return (
            gr.update(interactive=False),
            "📝 **Estat**: Afegiu una descripció del vostre treball per continuar",
        )

    # All conditions met
    return (
        gr.update(interactive=True),
        f"✅ **Estat**: Tot preparat! {len(valid_types)} imatge{'s' if len(valid_types) > 1 else ''} {'preparades' if len(valid_types) > 1 else 'preparada'} per analitzar",
    )

def format_analysis_results(result, classification, files, image_info):
    """Format the LLM results as plain text"""
    return result