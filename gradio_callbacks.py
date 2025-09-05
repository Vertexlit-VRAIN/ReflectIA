"""
Callback functions for the Gradio interface.
"""

import gradio as gr

from ai_providers import call_ai_model
from config import AI_PROVIDER, DEBUG_LLM_OUTPUT, DEBUG_MODE, MAX_IMAGES
from history_manager import load_history, save_history
from image_utils import encode_image_to_base64


def history_to_gradio_messages(history):
    """
    Convert our internal history schema to Gradio Chatbot messages,
    respecting the 'visible' flag.
    """
    msgs = []
    for m in history or []:
        if not m.get("visible", True):
            continue  # Skip messages marked as not visible

        role = m.get("role", "user")
        role = "assistant" if role in ("model", "assistant") else "user"
        parts = m.get("parts") or []
        texts = []
        for p in parts:
            if isinstance(p, str):
                texts.append(p)
        content = "\n\n".join(texts) if texts else "(missatge amb imatge)"
        msgs.append({"role": role, "content": content})
    return msgs


def generate_llm_response(
    user_id,
    files,
    classification,
    user_description,
    *type_selections,
    progress=gr.Progress(),
):
    if DEBUG_MODE:
        if user_id:
            h = load_history(user_id) or []
            h.append(
                {
                    "role": "user",
                    "parts": ["(DEBUG) Sol·licitud d'anàlisi"],
                    "visible": False,
                }
            )
            h.append({"role": "model", "parts": [DEBUG_LLM_OUTPUT], "visible": False})
            save_history(user_id, h)
        return DEBUG_LLM_OUTPUT


    if files:
        files = [f for f in files if f is not None]
    if not files:
        return "❌ **Error**: Si us plau, pugeu almenys una imatge per a l'anàlisi."

    if not user_id:
        return (
            "❌ **Error**: Si us plau, introduïu el vostre identificador d'estudiant."
        )

    if not classification:
        return "❌ **Error**: Si us plau, seleccioneu primer una classificació."

    valid_files = []
    valid_types = []
    for i, file in enumerate(files):
        if type_selections[i] is not None and type_selections[i] != "":
            valid_files.append(file)
            valid_types.append(type_selections[i])

    if not valid_files:
        return (
            "❌ **Error**: Si us plau, especifiqueu el tipus per a almenys una imatge."
        )

    images_base64 = []
    image_info = []

    for i, file in enumerate(valid_files):
        if hasattr(file, "name"):
            image_path = file.name
        else:
            image_path = str(file)

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

    if classification == "Pràctica 1. Revista":
        prompt_file = "prompts/prompt_magazine_full.txt"
    elif classification == "Pràctica 2. Xarxes Socials":
        prompt_file = "prompts/prompt_social_full.txt"
    else:
        return "❌ **Error**: Classificació no vàlida."

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        return f"❌ **Error**: No s'ha trobat el fitxer de prompt: {prompt_file}"

    context = f"Classificació: {classification}"
    if user_description and user_description.strip():
        context += f"\nDescripció de l'usuari: {user_description.strip()}"

    context += f"\nImatges a analitzar: {', '.join(image_info)}"

    prompt = f"""{base_prompt}

---
### CONTEXT ADICIONAL DE L'ALUMNE:
{context}

Analitza les imatges proporcionades seguint les directrius del prompt anterior.
"""

    history = load_history(user_id) or []

    result = call_ai_model(AI_PROVIDER, prompt, images_base64, history)

    history.append({"role": "user", "parts": [prompt], "visible": False})
    history.append({"role": "model", "parts": [result], "visible": False})

    save_history(user_id, history)

    return format_analysis_results(result, classification, files, image_info)


def update_type_dropdowns(files, classification):
    if files:
        files = [f for f in files if f is not None]
    image_count = len(files) if files else 0

    num_rows = (MAX_IMAGES + 1) // 2

    # ---- SAFE DEFAULTS when no classification selected ----
    if not classification:
        # rows hidden
        row_updates = [gr.update(visible=False)] * num_rows
        # all thumbs hidden and cleared
        image_updates = [gr.update(visible=False, value=None)] * MAX_IMAGES
        # all dropdowns hidden, value cleared, but choices set to a harmless non-empty list
        dropdown_updates = [
            gr.update(visible=False, choices=["—"], value=None)
        ] * MAX_IMAGES
        return row_updates + image_updates + dropdown_updates

    # ---- Type options depending on classification ----
    if classification == "Pràctica 1. Revista":
        type_options = ["Portada", "Pàgines interiors"]
    elif classification == "Pràctica 2. Xarxes Socials":
        type_options = [
            "Newsletter",
            "Instagram Artista",
            "Instagram Concurs",
            "X Artista",
            "X Concurs",
            "Logotip",
            "Capçelera",
        ]
    else:
        type_options = ["—"]

    # Start with everything hidden/cleared (safe)
    row_updates = [gr.update(visible=False)] * num_rows
    image_updates = [gr.update(visible=False, value=None)] * MAX_IMAGES
    dropdown_updates = [
        gr.update(visible=False, choices=["—"], value=None)
    ] * MAX_IMAGES

    # Reveal only the needed slots, with real choices
    for i in range(image_count):
        row_idx = i // 2
        if row_idx < num_rows:
            row_updates[row_idx] = gr.update(visible=True)

        image_updates[i] = gr.update(visible=True, value=files[i])

        filename = files[i].name if hasattr(files[i], "name") else f"Imatge {i + 1}"
        if "/" in filename:
            filename = filename.split("/")[-1]

        dropdown_updates[i] = gr.update(
            visible=True,
            choices=type_options,
            value=None,
            label=f"Tipus per a {filename}",
            show_label=False,
        )

    return row_updates + image_updates + dropdown_updates


# Removed auto_detect_image_type function - users must classify manually

def update_button_and_status(
    user_id, files, classification, user_description, *type_selections
):
    # Normalize inputs
    files = [f for f in (files or []) if f is not None]
    has_files = len(files) > 0
    has_id = bool(user_id)
    has_class = bool(classification)

    # Count valid types for the uploaded images
    sel = list(type_selections[: len(files)])
    valid_types = [t for t in sel if t is not None and t != ""]
    has_any_type = len(valid_types) > 0

    has_desc = bool(user_description and user_description.strip())

    ready = has_id and has_files and has_class and has_any_type and has_desc

    # Minimal, single-line hint (only when something is missing)
    missing = None
    if not has_id:
        missing = "Activa l’ID per començar."
    elif not has_files:
        missing = "Puja almenys una imatge."
    elif not has_class:
        missing = "Selecciona la classificació."
    elif not has_any_type:
        missing = "Assigna el tipus a alguna imatge."
    elif not has_desc:
        missing = "Afegeix una breu descripció."

    status_out = gr.update(value=f"ℹ️ {missing}" if missing else "", visible=not ready)

    return (gr.update(interactive=ready), status_out)

def format_analysis_results(result, classification, files, image_info):
    return result


def handle_conversation_message(message, history, user_id):
    """
    Handles messages from the conversation tab.
    """
    if not user_id:
        gr.Warning("Error: No s'ha trobat l'identificador d'usuari.")
        return history, gr.update(value=None)

    history = load_history(user_id) or []

    try:
        with open("prompts/prompt_conversation.txt", "r", encoding="utf-8") as f:
            conversation_prompt = f.read()
    except FileNotFoundError:
        gr.Warning("Error: No s'ha trobat el fitxer de prompt de conversa.")
        return history, gr.update(value=None)

    # Prepend the conversational prompt if it's the first conversational message
    is_first_conversation = not any(m.get("visible", False) for m in history)
    if is_first_conversation:
        system_prompt = [
            {"role": "user", "parts": [conversation_prompt], "visible": False},
            {
                "role": "model",
                "parts": [
                    "Hola! Soc el teu tutor de disseny. A partir de l'anàlisi inicial, podem conversar sobre el teu treball. Fes-me qualsevol pregunta o demana'm suggeriments."
                ],
                "visible": True,
            },
        ]
        history.extend(system_prompt)

    user_parts = []
    images_base64 = []

    text_input = ""
    if isinstance(message, dict):
        text_input = (message.get("text") or "").strip()
    elif isinstance(message, str):
        text_input = message.strip()

    if text_input:
        user_parts.append(text_input)

    if isinstance(message, dict):
        for file_obj in message.get("files") or []:
            file_path = file_obj if isinstance(file_obj, str) else file_obj.get("path")
            if file_path:
                img_bytes = encode_image_to_base64(file_path)
                if "error" not in img_bytes:
                    user_parts.append(img_bytes)
                    images_base64.append(img_bytes)
                else:
                    gr.Warning(f"Error processing image: {img_bytes['error']}")

    if not user_parts:
        return history_to_gradio_messages(history), gr.update(value=None)

    history.append({"role": "user", "parts": user_parts, "visible": True})

    if DEBUG_MODE:
        response = (
            "🧪 **Mode debug**\n\n"
            f"Text rebut: {text_input or '(cap text)'}\n"
            f"Imatges adjuntes: {len(images_base64)}"
        )
    else:
        response = call_ai_model(
            AI_PROVIDER, "", images_base64=images_base64, history=history
        )

    history.append({"role": "model", "parts": [response], "visible": True})
    save_history(user_id, history)

    return history_to_gradio_messages(history), gr.update(value=None, interactive=True)

def ensure_conversation_intro(user_id):
    """
    Ensure the tutor's intro message is present and visible so the chat
    shows a welcome immediately after analysis unlocks.
    """
    history = load_history(user_id) or []
    # If there is already any visible message, keep it.
    has_visible = any(m.get("visible", False) for m in history)
    if not has_visible:
        history.append({
            "role": "model",
            "parts": [
                "Hola! Soc el teu tutor de disseny. A partir de l'anàlisi inicial, podem conversar sobre el teu treball. Fes-me qualsevol pregunta o demana'm suggeriments."
            ],
            "visible": True,
        })
        save_history(user_id, history)
    return history_to_gradio_messages(history)
