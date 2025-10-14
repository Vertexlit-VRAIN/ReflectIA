"""
Callback functions for the Gradio interface.
"""

import gradio as gr
import os, shutil

from ai_providers import call_ai_model
from config import (
    AI_PROVIDER,
    DEBUG_LLM_OUTPUT,
    DEBUG_MODE,
    MAX_IMAGES,
    PROMPT_MAGAZINE,
    PROMPT_SOCIAL,
    PROMPT_CONVERSATION,
)
from image_utils import encode_image_to_base64

from history_manager import (
    load_history,
    save_history,
    load_state,
    save_state,
    get_user_files_dir,
)
# New helper imports to support tag-aware restore
from history_manager import get_last_message_with_flag, extract_text_from_parts


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
        return (
            "❌ **Error**: Si us plau, introduïu el vostre identificador d'estudiant."
        )

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

    # === STEP 0: LOAD AND PARSE PROMPT ===
    if classification == "Pràctica 1. Revista":
        prompt_file = PROMPT_MAGAZINE
    elif classification == "Pràctica 2. Xarxes Socials":
        prompt_file = PROMPT_SOCIAL
    else:
        return "❌ **Error**: Classificació no vàlida."

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            full_prompt_content = f.read()
    except FileNotFoundError:
        return f"❌ **Error**: No s'ha trobat el fitxer de prompt: {prompt_file}"

    separator = "### Whole-Project (Conjunto) Analysis"
    if separator not in full_prompt_content:
        return f"❌ **Error**: El fitxer de prompt '{prompt_file}' no conté el separador necessari: '{separator}'."

    prompt_parts = full_prompt_content.split(separator, 1)
    image_analysis_prompt_base = prompt_parts[0]
    global_analysis_prompt_base = separator + prompt_parts[1]

    # --- Main difference: AI call vs. placeholder ---
    if DEBUG_MODE:
        result = DEBUG_LLM_OUTPUT
    else:
        all_individual_results_raw = [] # CHANGE: Store raw results first
        num_images = len(persisted_paths)
        progress(0, desc="Iniciant anàlisi...")

        # === STEP 1: INDIVIDUAL IMAGE ANALYSIS ===
        # This loop completes entirely before proceeding to the next step.
        for i, path in enumerate(persisted_paths):
            filename = os.path.basename(path)
            image_type = types[i]
            
            progress((i) / (num_images + 1), desc=f"Analitzant imatge {i + 1}/{num_images}: {filename}")

            image_b64 = encode_image_to_base64(path)
            if isinstance(image_b64, dict) and "error" in image_b64:
                return image_b64["error"]
            
            image_context = (
                f"Student's overall description: {user_description.strip()}\n"
                f"Now, focus EXCLUSIVELY on the following image:\n"
                f"- Filename: {filename}\n"
                f"- Assigned type: {image_type}"
            )

            prompt_for_this_image = f"""{image_analysis_prompt_base}

---
### IMAGE TO ANALYZE

{image_context}

Provide your detailed analysis for THIS SPECIFIC IMAGE, following the guidelines from the 'Procedure for Image-by-Image Analysis' section. Start your response directly with the analysis.
"""
            single_result = call_ai_model(
                AI_PROVIDER, 
                prompt_for_this_image, 
                images_base64=[image_b64], 
                history=None
            )
            if "❌ **Error" in single_result:
                return f"Error analyzing '{filename}': {single_result}"

            # CHANGE: Append only the raw AI response, not the pre-formatted string.
            all_individual_results_raw.append(single_result)

        # === STEP 2: GLOBAL CONSISTENCY ANALYSIS ===
        # This step only runs AFTER the loop above is 100% complete.
        progress(num_images / (num_images + 1), desc="Generant anàlisi global...")
        
        # CHANGE: Use the raw results to build the context. This ensures all images are included.
        combined_individual_analyses_text = "\n\n---\n\n".join(all_individual_results_raw)
        
        global_analysis_prompt = f"""{global_analysis_prompt_base}

---
### CONTEXT: YOUR PREVIOUSLY GENERATED ANALYSES

You have already analyzed the individual pieces. Here are your complete findings for each one:

{combined_individual_analyses_text}

---
Now, using the instructions from the first part of this prompt (Whole-Project Analysis) and the context of your individual analyses above, provide the final "Whole-Project Analysis (Conjunto)".
"""

        global_result = call_ai_model(
            AI_PROVIDER,
            global_analysis_prompt,
            images_base64=None, # No images needed for this call
            history=None
        )

        if "❌ **Error" in global_result:
            return f"Error generating global analysis: {global_result}"

        # === STEP 3: ASSEMBLE FINAL REPORT IN THE CORRECT ORDER ===
        # This is the corrected, robust assembly process.
        progress(1.0, desc="Anàlisi completada!")
        
        # 1. Build the individual analysis section from the raw data, ensuring correct order.
        final_report_body = "## 🤖 Anàlisi Imatge per Imatge\n\n"
        for i, raw_result in enumerate(all_individual_results_raw):
            filename = os.path.basename(persisted_paths[i])
            image_type = types[i]
            final_report_body += f"### Anàlisi de '{filename}' ({image_type})\n\n{raw_result}\n\n---\n\n"
        
        # 2. Append the global analysis section at the very end.
        final_report_global = f"## 🌍 Anàlisi Global del Projecte (Conjunto)\n\n{global_result}"
        
        # 3. Combine them into the final result.
        result = f"{final_report_body.strip()}\n\n{final_report_global}"

        # --- History Management ---
        history = load_history(user_id) or []
        history.append({
            "role": "user",
            "parts": [full_prompt_content],
            "visible": False,
            "analysis": True
        })
        history.append({
            "role": "model",
            "parts": [result],
            "visible": False,
            "analysis": True
        })
        save_history(user_id, history)

    # --- Persist full state ---
    save_state(
        user_id,
        {
            "classification": classification,
            "description": user_description,
            "files": [
                {"path": persisted_paths[i], "type": types[i]}
                for i in range(len(persisted_paths))
            ],
            "analysis": result,
        },
    )

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
            "Capçalera",
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


def update_button_and_status(
    user_id, files, classification, user_description, *type_selections
):
    files = [f for f in (files or []) if f is not None]
    has_files = len(files) > 0
    has_id = bool(user_id)
    has_class = bool(classification)
    has_desc = bool(user_description and user_description.strip())

    needed = len(files)
    typed_ok = True
    for i in range(needed):
        t = type_selections[i] if i < len(type_selections) else None
        if t is None or str(t).strip() == "":
            typed_ok = False
            break

    ready = has_id and has_files and has_class and typed_ok and has_desc
    return gr.update(interactive=ready)


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
            {"role": "user", "parts": [conversation_prompt], "visible": False, "system": True},
            {
                "role": "model",
                "parts": [
                    "Hola! A partir de l'anàlisi inicial, podem conversar sobre el teu treball. Fes-me qualsevol pregunta o demana'm suggeriments."
                ],
                "visible": True,
                "conversation": True,
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

    history.append({
        "role": "user",
        "parts": user_parts,
        "visible": True,
        "conversation": True
    })

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

    history.append({
        "role": "model",
        "parts": [response],
        "visible": True,
        "conversation": True
    })
    save_history(user_id, history)

    return history_to_gradio_messages(history), gr.update(value=None, interactive=True)


def ensure_conversation_intro(user_id):
    history = load_history(user_id) or []
    has_visible = any(m.get("visible", False) for m in history)
    if not has_visible:
        try:
            with open(PROMPT_CONVERSATION, "r", encoding="utf-8") as f:
                conversation_prompt = f.read()
        except FileNotFoundError:
            conversation_prompt = (
                "Ets un tutor de disseny que dona feedback als estudiants."
            )

        system_prompt = {
            "role": "user",
            "parts": [conversation_prompt],
            "visible": False,
            "system": True,
        }
        history.append(system_prompt)

        greeting = {
            "role": "model",
            "parts": [
                "Hola! A partir de l'anàlisi inicial, podem conversar sobre el teu treball. "
                "Fes-me qualsevol pregunta o demana'm suggeriments."
            ],
            "visible": True,
            "conversation": True,
        }
        history.append(greeting)

        save_history(user_id, history)

    return history_to_gradio_messages(history)


def restore_config_for_user(user_id, max_images=MAX_IMAGES):
    state = load_state(user_id) or {
        "classification": None,
        "description": "",
        "files": [],
        "analysis": "Pugeu imatges, seleccioneu classificació i cliqueu **“🔍 Analitzar”**…",
    }
    classification_val = state.get("classification")
    description_val = state.get("description") or ""

    last_analysis_msg = get_last_message_with_flag(user_id, "analysis")
    last_analysis_text = extract_text_from_parts(last_analysis_msg) if last_analysis_msg else ""
    analysis_val = (
        last_analysis_text
        or state.get("analysis")
        or "Pugeu imatges, seleccioneu classificació i cliqueu **“🔍 Analitzar”**…"
    )

    file_paths = [f.get("path") for f in (state.get("files") or []) if f.get("path")]
    types = [f.get("type") for f in (state.get("files") or [])]

    dd_values = []
    for i in range(max_images):
        v = types[i] if i < len(types) else None
        dd_values.append(gr.update(value=v))

    if file_paths:
        first_filename = os.path.basename(file_paths[0])
        filename_update = gr.update(value=f"**{first_filename}**", visible=True)
    else:
        filename_update = gr.update(value="", visible=False)

    return (
        classification_val,
        file_paths,
        description_val,
        analysis_val,
        *dd_values,
        file_paths,
        filename_update,
    )


def disable_analyze_if_done(user_id):
    state = load_state(user_id) or {}
    if state.get("analysis"):
        return gr.update(interactive=False)
    return gr.update()
