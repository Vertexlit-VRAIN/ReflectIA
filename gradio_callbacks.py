"""
Callback functions for the Gradio interface.
"""

import gradio as gr

from ai_providers import call_ai_model
from config import AI_PROVIDER, DEBUG_LLM_OUTPUT, DEBUG_MODE, MAX_IMAGES, PROMPT_MAGAZINE, PROMPT_SOCIAL, PROMPT_CONVERSATION
from image_utils import encode_image_to_base64

import os, shutil
from history_manager import (
    load_history,
    save_history,
    load_state,
    save_state,
    get_user_files_dir,
)


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
    # --- Validation (shared for debug & normal) ---
    if files:
        files = [f for f in files if f is not None]
    if not files:
        return "❌ **Error**: Si us plau, pugeu almenys una imatge per a l'anàlisi."

    if not user_id:
        return "❌ **Error**: Si us plau, introduïu el vostre identificador d'estudiant."

    if not classification:
        return "❌ **Error**: Si us plau, seleccioneu primer una classificació."

    types = []
    for i, file in enumerate(files):
        t = type_selections[i] if i < len(type_selections) else None
        types.append(t)

    if not all(t not in (None, "") for t in types):
        return "❌ **Error**: Assigna una categoria a **cada** imatge."

    # --- Persist copies of uploaded files ---
    user_dir = get_user_files_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    persisted_paths = []
    for f in files:
        src = f.name if hasattr(f, "name") else str(f)
        if not src or not os.path.exists(src):
            continue
        dst = os.path.join(user_dir, os.path.basename(src))
        if os.path.abspath(src) != os.path.abspath(dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                dst = src
        persisted_paths.append(dst)

    # --- Prepare prompt (shared) ---
    if classification == "Pràctica 1. Revista":
        prompt_file = PROMPT_MAGAZINE
    elif classification == "Pràctica 2. Xarxes Socials":
        prompt_file = PROMPT_SOCIAL
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
    context += f"\nImatges a analitzar: {', '.join(os.path.basename(p) + ' - ' + str(types[i]) for i, p in enumerate(persisted_paths))}"

    prompt = f"""{base_prompt}

---
### CONTEXT ADICIONAL DE L'ALUMNE:
{context}

Analitza les imatges proporcionades seguint les directrius del prompt anterior.
"""

    # --- Main difference: AI call vs. placeholder ---
    if DEBUG_MODE:
        result = DEBUG_LLM_OUTPUT
    else:
        # Encode for model
        images_base64 = []
        for p in persisted_paths:
            b64 = encode_image_to_base64(p)
            if isinstance(b64, dict) and "error" in b64:
                return b64["error"]
            images_base64.append(b64)

        history = load_history(user_id) or []
        result = call_ai_model(AI_PROVIDER, prompt, images_base64, history)

        # Append invisible history
        history.append({"role": "user", "parts": [prompt], "visible": False})
        history.append({"role": "model", "parts": [result], "visible": False})
        save_history(user_id, history)

    # --- Persist full state (identical for both modes) ---
    save_state(user_id, {
        "classification": classification,
        "description": user_description,
        "files": [{"path": persisted_paths[i], "type": types[i]} for i in range(len(persisted_paths))],
        "analysis": result,
    })

    return result


def update_type_dropdowns(files, classification):
    if files:
        files = [f for f in files if f is not None]
    image_count = len(files) if files else 0

    num_rows = (MAX_IMAGES + 1) // 2

    if not classification:
        row_updates = [gr.update(visible=False)] * num_rows
        image_updates = [gr.update(visible=False, value=None)] * MAX_IMAGES
        dropdown_updates = [gr.update(visible=False, choices=["—"])] * MAX_IMAGES
        return row_updates + image_updates + dropdown_updates

    if classification == "Pràctica 1. Revista":
        type_options = ["Portada", "Pàgines interiors", "Contraportada"]
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

    row_updates = [gr.update(visible=False)] * num_rows
    image_updates = [gr.update(visible=False, value=None)] * MAX_IMAGES
    dropdown_updates = [gr.update(visible=False, choices=["—"])] * MAX_IMAGES

    for i in range(image_count):
        row_idx = i // 2
        if row_idx < num_rows:
            row_updates[row_idx] = gr.update(visible=True)

        image_updates[i] = gr.update(visible=True, value=files[i])

        filename = files[i].name if hasattr(files[i], "name") else f"Imatge {i + 1}"
        if "/" in filename:
            filename = filename.split("/")[-1]

        # NOTE: do NOT pass value=... so restored values persist
        dropdown_updates[i] = gr.update(
            visible=True,
            choices=type_options,
            label=f"Tipus per a {filename}",
            show_label=False,
        )

    return row_updates + image_updates + dropdown_updates


# Removed auto_detect_image_type function - users must classify manually

def update_button_and_status(
    user_id, files, classification, user_description, *type_selections
):
    # Normalize
    files = [f for f in (files or []) if f is not None]
    has_files = len(files) > 0
    has_id = bool(user_id)
    has_class = bool(classification)
    has_desc = bool(user_description and user_description.strip())

    # Cada imatge ha de tenir tipus (no nuls / no buits)
    needed = len(files)
    selected = []
    for i in range(needed):
        t = type_selections[i] if i < len(type_selections) else None
        if t is not None and str(t).strip() != "":
            selected.append(t)
    all_typed = (len(selected) == needed) and needed > 0

    ready = has_id and has_files and has_class and all_typed and has_desc

    # Missatge mínim quan falta alguna cosa
    missing = None
    if not has_id:
        missing = "Activa l’ID per començar."
    elif not has_class:
        missing = "Selecciona la pràctica."
    elif not has_files:
        missing = "Puja almenys una imatge."
    elif not all_typed:
        missing = "Assigna una categoria a **cada** imatge."
    elif not has_desc:
        missing = "Afegeix una breu descripció del disseny."

    status_out = gr.update(value=f"{missing}" if missing else "", visible=not ready)
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
        with open(PROMPT_CONVERSATION, "r", encoding="utf-8") as f:
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
    Ensure both the system conversational prompt and the tutor's greeting
    are present in history so the model starts with the right instructions.
    """
    history = load_history(user_id) or []
    has_visible = any(m.get("visible", False) for m in history)
    if not has_visible:
        # Load system conversational prompt
        try:
            with open(PROMPT_CONVERSATION, "r", encoding="utf-8") as f:
                conversation_prompt = f.read()
        except FileNotFoundError:
            conversation_prompt = "Ets un tutor de disseny que dona feedback als estudiants."

        # Inject hidden system prompt for the model
        system_prompt = {
            "role": "user",
            "parts": [conversation_prompt],
            "visible": False,
        }
        history.append(system_prompt)

        # Inject visible greeting for the student
        greeting = {
            "role": "model",
            "parts": [
                "Hola! Soc el teu tutor de disseny. A partir de l'anàlisi inicial, podem conversar sobre el teu treball. "
                "Fes-me qualsevol pregunta o demana'm suggeriments."
            ],
            "visible": True,
        }
        history.append(greeting)

        save_history(user_id, history)

    return history_to_gradio_messages(history)

def restore_config_for_user(user_id, max_images=MAX_IMAGES):
    """
    Loads states/<id>.json and returns:
    - classification value
    - files value (list of paths)
    - user_description value
    - llm_output value (analysis)
    - one output per type dropdown (value for each, length = MAX_IMAGES)
    """
    state = load_state(user_id) or {
        "classification": None,
        "description": "",
        "files": [],
        "analysis": "Pugeu imatges, seleccioneu classificació i cliqueu **“🔍 Analitzar”**…",
    }
    classification_val = state.get("classification")
    description_val = state.get("description") or ""
    analysis_val = state.get("analysis") or "Pugeu imatges, seleccioneu classificació i cliqueu **“🔍 Analitzar”**…"
    file_paths = [f.get("path") for f in (state.get("files") or []) if f.get("path")]
    types = [f.get("type") for f in (state.get("files") or [])]

    # Build dropdown value updates up to MAX_IMAGES
    dd_values = []
    for i in range(max_images):
        v = types[i] if i < len(types) else None
        dd_values.append(gr.update(value=v))

    return (classification_val, file_paths, description_val, analysis_val, *dd_values)

def disable_analyze_if_done(user_id):
    """
    If analysis is already saved for this user, disable the analyze button.
    Otherwise, leave it unchanged.
    """
    state = load_state(user_id) or {}
    if state.get("analysis"):
        return gr.update(interactive=False)
    return gr.update()  # no change
