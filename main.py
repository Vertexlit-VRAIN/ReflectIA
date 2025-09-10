"""
Main application for AI Image Analysis.

This script launches a Gradio interface for analyzing images based on different
classifications (e.g., Editorial, Social Network).
"""

import gradio as gr
import time

from config import MAX_IMAGES, DEBUG_FAKE_WAIT_SECONDS
from gradio_callbacks import (
    generate_llm_response,
    handle_conversation_message,
    history_to_gradio_messages,
    update_button_and_status,
    update_type_dropdowns,
    ensure_conversation_intro,  # used to inject the tutor greeting on unlock
)
from history_manager import load_history

# (Kept for reference; no longer used as an accordion)
PENDING_LABEL = "🔴 ID pendent"
ACTIVE_LABEL_PREFIX = "🟢 ID actiu"


def _load_custom_css(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _toggle_confirm(uid_text):
    """Enable the confirm button only when there is some ID typed."""
    uid = (uid_text or "").strip()
    return gr.update(interactive=bool(uid))


def commit_id(uid_text):
    uid = (uid_text or "").strip()
    history = load_history(uid) or []

    has_visible   = any(m.get("visible", False) for m in history)
    has_any_model = any(m.get("role") in ("model", "assistant") for m in history)

    if uid and (has_visible or has_any_model):
        if not has_visible:
            chat_messages = ensure_conversation_intro(uid)
        else:
            chat_messages = history_to_gradio_messages(history)
        composer_update = gr.update(interactive=True)
        analysis_tab_update = gr.update(interactive=True)
        tabs_update = gr.update(visible=True, selected="analysis")   # ⬅️ go directly
    else:
        chat_messages = history_to_gradio_messages(history)
        composer_update = gr.update(interactive=False)
        analysis_tab_update = gr.update(interactive=False)
        tabs_update = gr.update(visible=True, selected="config")     # default to config

    if uid:
        id_block_update = gr.update(visible=False)
        input_update  = gr.update(visible=False)
        button_update = gr.update(visible=False)
        content_update = gr.update(visible=False, value=f"**{uid}**")
    else:
        id_block_update = gr.update(visible=True)
        input_update  = gr.update(visible=True)
        button_update = gr.update(visible=True)
        content_update = gr.update(visible=False)

    return (
        id_block_update,      # id_block
        tabs_update,          # tabs_wrapper (now includes selected)
        composer_update,      # composer
        uid,                  # active_user_id
        chat_messages,        # chat
        analysis_tab_update,  # analysis_tab interactive
        input_update,         # user_id_input
        button_update,        # confirm_id_btn
        content_update,       # id_content
    )


def analyze_and_close(uid, files_v, classification_v, user_desc, *type_sel):
    """
    3-step generator:
      1) Show overlay
      2) Return results + enable & select Analysis tab + unlock composer + hide overlay
      3) (Optional) no-op or additional UI polish
    """
    # Step 1: show overlay / loading
    yield (
        "**Analitzant les imatges..., espereu un moment**",  # llm_output
        [],                                                  # chat
        gr.update(),                                         # analysis_tab (no change yet)
        gr.update(),                                         # composer
        gr.update(),                                         # tabs_wrapper
        gr.update(visible=True),                             # wait_overlay
    )

    if DEBUG_FAKE_WAIT_SECONDS and DEBUG_FAKE_WAIT_SECONDS > 0:
        time.sleep(DEBUG_FAKE_WAIT_SECONDS)

    # Work real (or DEBUG_LLM_OUTPUT if DEBUG_MODE=True)
    text = generate_llm_response(uid, files_v, classification_v, user_desc, *type_sel)
    chat_messages = ensure_conversation_intro(uid)

    # Step 2: results + unlock composer + enable & select Analysis tab + hide overlay
    # IMPORTANT ORDER for Gradio 5: first make the tab interactive, THEN select it on the Tabs container.
    yield (
        text,                                               # llm_output
        chat_messages,                                      # chat
        gr.update(interactive=True),                        # analysis_tab -> enable
        gr.update(interactive=True),                        # composer -> unlock
        gr.update(selected="analysis"),                     # tabs_wrapper -> SELECT "Anàlisi" tab by id
        gr.update(visible=False),                           # wait_overlay -> hide
    )

    # Step 3: (Optional) nothing else to change; keeping generator signature
    yield (
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),  # leave currently selected tab as-is
        gr.update(),
    )


def main():
    custom_css = _load_custom_css("static/styles.css")

    # Keep copy-protection for chat area
    chat_protection_js = """
    <script>
    function preventChatCopy() {
        const chatElements = document.querySelectorAll('.chatbot-surface, .gr-chatbot, .chatbot-surface *, .gr-chatbot *');
        chatElements.forEach(element => {
            element.addEventListener('selectstart', function(e) { e.preventDefault(); return false; });
            element.addEventListener('contextmenu', function(e) { e.preventDefault(); return false; });
            element.addEventListener('dragstart', function(e) { e.preventDefault(); return false; });
            element.addEventListener('copy', function(e) { e.preventDefault(); return false; });
            element.addEventListener('cut', function(e) { e.preventDefault(); return false; });
        });
    }
    document.addEventListener('DOMContentLoaded', function(){
      preventChatCopy();
      const observer = new MutationObserver(preventChatCopy);
      observer.observe(document.body, { childList: true, subtree: true });
    });
    </script>
    """
    custom_css += chat_protection_js

    with gr.Blocks(
        title="AI Image Analysis",
        theme="Taithrah/Minimal",
        css=custom_css,
    ) as demo:
        active_user_id = gr.State("")

        wait_overlay = gr.HTML(
            """
            <div class="wait-overlay">
              <div class="wait-card">
                <div class="wait-title">Analitzant…</div>
                <div class="wait-bar"><span class="bar"></span></div>
                <div class="wait-tip">Açò pot trigar uns segons</div>
              </div>
            </div>
            """,
            visible=False,
        )

        # ---------- Global ID block (no accordion) ----------
        with gr.Column(elem_classes=["id-block"]) as id_block:
            gr.Markdown(
                """# Introdueix el teu ID
        Aquest identificador s’utilitzarà per a poder desar i recuperar la conversa"""
            )
            id_content = gr.Markdown("", visible=False)
            with gr.Row(elem_classes=["id-input-row"]):
                user_id_input = gr.Textbox(
                    placeholder="Escriu el teu ID…",
                    show_label=False,
                    lines=1,
                    max_lines=1,
                    elem_classes=["emphasized-input", "larger-font", "id-textbox"],
                    scale=4,
                )
                confirm_id_btn = gr.Button(
                    "Començar",
                    variant="primary",
                    size="lg",
                    elem_classes=["purple-button", "id-confirm-btn"],
                    interactive=False,
                    scale=1,
                )

        # ---------- Tabs (use gr.Tabs + gr.Tab with ids) ----------
        with gr.Tabs(elem_classes=["main-tabs"], visible=False) as tabs_wrapper:
            with gr.Tab("Configuració", id="config"):
                # 1) Classification
                gr.Markdown("### 1. Selecciona la pràctica", elem_classes=["section-title"])
                classification = gr.Dropdown(
                    choices=["Pràctica 1. Revista", "Pràctica 2. Xarxes Socials"],
                    label="📋 Classificació d'Imatges",
                    show_label=False,
                    value=None,
                    elem_classes=["visible-dropdown", "with-info", "larger-font", "section-card"],
                )

                # 2) Upload
                gr.Markdown("### 2. Puja les imatges", elem_classes=["section-title"])
                with gr.Row(elem_classes=["section-card"]):
                    with gr.Column(scale=4):
                        files = gr.File(
                            file_count="multiple",
                            file_types=["image"],
                            label="📸 Afegir imatges",
                            height=200,
                            elem_id="file-uploader",
                            elem_classes=["large-upload-button"],
                        )

                # 3) Tag each image
                gr.Markdown("### 3. Assigna la categoria corresponent a cada imatge", elem_classes=["section-title"])
                with gr.Row(elem_classes=["section-card"]):
                    rows, thumbnail_images, type_dropdowns = [], [], []
                    for i in range(0, MAX_IMAGES, 2):
                        with gr.Row(visible=False) as row:
                            rows.append(row)

                            # Left slot
                            with gr.Column(scale=1, min_width=360):
                                with gr.Row(elem_classes=["thumbline"]):
                                    with gr.Column(scale=1, min_width=160):
                                        thumb_a = gr.Image(
                                            type="filepath",
                                            label=f"Image {i + 1}",
                                            height=150,
                                            width=150,
                                            visible=False,
                                            interactive=False,
                                            show_label=False,
                                            elem_classes=["thumbnail-container"],
                                        )
                                    with gr.Column(scale=1, min_width=180, elem_classes=["vcenter-col"]):
                                        dd_a = gr.Dropdown(
                                            choices=[],
                                            label=f"Tipus per a Imatge {i + 1}",
                                            value=None,
                                            visible=False,
                                            show_label=False,
                                            elem_classes=["visible-dropdown", "medium-font"],
                                            allow_custom_value=True,
                                        )
                                thumbnail_images.append(thumb_a)
                                type_dropdowns.append(dd_a)

                            # Right slot
                            with gr.Column(scale=1, min_width=360):
                                with gr.Row(elem_classes=["thumbline"]):
                                    with gr.Column(scale=1, min_width=160):
                                        thumb_b = gr.Image(
                                            type="filepath",
                                            label=f"Image {i + 2}",
                                            height=150,
                                            width=150,
                                            visible=False,
                                            interactive=False,
                                            show_label=False,
                                            elem_classes=["thumbnail-container"],
                                        )
                                    with gr.Column(scale=1, min_width=180, elem_classes=["vcenter-col"]):
                                        dd_b = gr.Dropdown(
                                            choices=[],
                                            label=f"Tipus per a Imatge {i + 2}",
                                            value=None,
                                            visible=False,
                                            show_label=False,
                                            elem_classes=["visible-dropdown", "medium-font"],
                                            allow_custom_value=True,
                                        )
                                thumbnail_images.append(thumb_b)
                                type_dropdowns.append(dd_b)

                # 4) Description
                gr.Markdown("### 4. Descriu el disseny", elem_classes=["section-title"])
                user_description = gr.Textbox(
                    label="📝 Descripció",
                    placeholder="Descriu aquella informació rellevant per a l’anàlisi, com per exemple: la temàtica escollida, què es vol transmetre, l’estil gràfic que es busca plasmar...",
                    lines=3,
                    max_lines=5,
                    show_label=False,
                    elem_classes=["emphasized-input", "with-info", "larger-font", "section-card"],
                )

                # Minimal hint + centered Analyze button
                with gr.Row(elem_classes=["analyze-bar"]):
                    status_message = gr.Markdown(
                        value="",
                        visible=False,
                        elem_classes=["status-message"],
                    )
                with gr.Row(elem_classes=["analyze-bar"]):
                    analyze_btn = gr.Button(
                        "🔍 Analitzar",
                        variant="primary",
                        interactive=False,
                        size="lg",
                        elem_classes=["purple-button", "analyze-cta"],
                    )

                # Results area
                gr.Markdown("## 🤖 Resultats de l'Anàlisi IA", elem_classes=["analysis-title"])
                llm_output = gr.Markdown(
                    value="Pugeu imatges, seleccioneu classificació i cliqueu **“🔍 Analitzar”**…",
                    elem_classes=["analysis-section", "llm-output", "result-card"],
                )

            # ===== Tab: Anàlisi (chat) — rendered but disabled until analysis done =====
            with gr.Tab("Anàlisi", id="analysis", interactive=False) as analysis_tab:
                chat = gr.Chatbot(
                    type="messages",
                    label="Sessió de tutoria",
                    height=640,
                    elem_classes=["chatbot-surface"],
                )
                composer = gr.MultimodalTextbox(
                    placeholder="Escriu un missatge o adjunta imatges…",
                    file_count="multiple",
                    file_types=["image"],
                    show_label=False,
                    interactive=False,  # unlocked after analysis
                )
                composer.submit(
                    fn=handle_conversation_message,
                    inputs=[composer, chat, active_user_id],
                    outputs=[chat, composer],
                )

        # ---------- Event wiring ----------

        confirm_id_btn.click(
            fn=commit_id,
            inputs=[user_id_input],
            outputs=[
                id_block,        # 0
                tabs_wrapper,    # 1
                composer,        # 2
                active_user_id,  # 3
                chat,            # 4
                analysis_tab,    # 5 (enable/disable tab via interactive)
                user_id_input,   # 6
                confirm_id_btn,  # 7
                id_content,      # 8
            ],
        )
        user_id_input.submit(
            fn=commit_id,
            inputs=[user_id_input],
            outputs=[
                id_block,
                tabs_wrapper,
                composer,
                active_user_id,
                chat,
                analysis_tab,
                user_id_input,
                confirm_id_btn,
                id_content,
            ],
        )

        # Enable/disable confirm button as the user types
        user_id_input.change(
            fn=_toggle_confirm,
            inputs=[user_id_input],
            outputs=[confirm_id_btn],
        )

        # collect the dynamic outputs for thumbs + dropdowns
        all_outputs = rows + thumbnail_images + type_dropdowns

        # 1) CLASSIFICATION change: update UI, then recompute status
        classification.change(
            fn=update_type_dropdowns,
            inputs=[files, classification],
            outputs=all_outputs,
        ).then(
            fn=update_button_and_status,
            inputs=[active_user_id, files, classification, user_description] + type_dropdowns,
            outputs=[analyze_btn, status_message],
        )

        # 2) FILES change (upload/delete): update UI, then recompute status
        files.change(
            fn=update_type_dropdowns,
            inputs=[files, classification],
            outputs=all_outputs,
        ).then(
            fn=update_button_and_status,
            inputs=[active_user_id, files, classification, user_description] + type_dropdowns,
            outputs=[analyze_btn, status_message],
        )

        # 3) Any field change should recompute status
        for component in [files, classification, user_description] + type_dropdowns:
            component.change(
                fn=update_button_and_status,
                inputs=[active_user_id, files, classification, user_description] + type_dropdowns,
                outputs=[analyze_btn, status_message],
            )

        # 4) Analyze click triggers LLM + updates chat + unlocks composer + enables & selects Anàlisi tab (3-step)
        analyze_btn.click(
            fn=analyze_and_close,
            inputs=[active_user_id, files, classification, user_description] + type_dropdowns,
            outputs=[llm_output, chat, analysis_tab, composer, tabs_wrapper, wait_overlay],
        )

    demo.launch(debug=True)


if __name__ == "__main__":
    main()
