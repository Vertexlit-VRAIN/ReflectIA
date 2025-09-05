"""
Main application for AI Image Analysis.

This script launches a Gradio interface for analyzing images based on different
classifications (e.g., Editorial, Social Network).
"""

import gradio as gr

from config import MAX_IMAGES
from gradio_callbacks import (
    generate_llm_response,
    handle_conversation_message,
    history_to_gradio_messages,
    update_button_and_status,
    update_type_dropdowns,
)
from history_manager import load_history

# Labels for the global ID accordion
PENDING_LABEL = "🔴 ID pendent"
ACTIVE_LABEL_PREFIX = "🟢 ID actiu"


def _load_custom_css(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def commit_id(uid_text):
    uid = (uid_text or "").strip()
    history = load_history(uid) or []
    chat_messages = history_to_gradio_messages(history)

    if uid:
        acc_update = gr.update(label=f"{ACTIVE_LABEL_PREFIX}", open=False)
        content_update = gr.update(value=f"**{uid}**", visible=True)
        input_update = gr.update(visible=False)  # hide text input
        button_update = gr.update(visible=False)  # hide button
    else:
        acc_update = gr.update(label=PENDING_LABEL, open=True)
        content_update = gr.update(visible=False)
        input_update = gr.update(visible=True)  # show text input
        button_update = gr.update(visible=True)  # show button

    return (
        acc_update,  # accordion update
        gr.update(visible=bool(uid)),  # tabs visibility
        gr.update(interactive=bool(uid)),  # composer active
        uid,  # active_user_id
        chat_messages,  # chat history formatted for Chatbot
        input_update,  # user_id_input visibility
        button_update,  # confirm_id_btn visibility
        content_update,  # id_content update
    )


def analyze_and_close(uid, files_v, classification_v, user_desc, *type_sel):
    # First return loading state (no accordion to close anymore)
    yield ("**Analitzant les imatges..., espereu un moment**", [])

    # Then process and return results
    text = generate_llm_response(uid, files_v, classification_v, user_desc, *type_sel)
    history = load_history(uid) or []
    chat_messages = history_to_gradio_messages(history)
    yield text, chat_messages


def main():
    custom_css = _load_custom_css("static/styles.css")

    # Add JavaScript to prevent text copying in chat
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
    
    // Run when page loads and when new content is added
    document.addEventListener('DOMContentLoaded', preventChatCopy);
    const observer = new MutationObserver(preventChatCopy);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """

    custom_css += chat_protection_js

    with gr.Blocks(
        title="AI Image Analysis", theme="Taithrah/Minimal", css=custom_css
    ) as demo:
        active_user_id = gr.State("")

        # ---------- Global ID accordion ----------
        with gr.Accordion(PENDING_LABEL, open=True) as id_accordion:
            with gr.Row(elem_classes=["id-row"]):
                with gr.Column(scale=4, elem_classes=["with-info"]):
                    gr.Markdown("#### 🧑‍🎓 Identificador d'Estudiant")
                    id_content = gr.Markdown(
                        "",
                        visible=False,
                    )
                    user_id_input = gr.Textbox(
                        placeholder="Escriu el teu ID…",
                        show_label=False,
                        lines=1,
                        max_lines=1,
                        elem_classes=["emphasized-input", "larger-font"],
                    )
                    confirm_id_btn = gr.Button(
                        "✓ Activar ID",
                        variant="primary",
                        size="lg",
                        elem_classes=["purple-button"],
                    )

        # ---------- Tabs ----------
        with gr.Tabs(elem_classes=["main-tabs"], visible=False) as tabs_wrapper:
            # ----- Tab: Anàlisi -----
            with gr.TabItem("Configuració"):
                # (Accordion "Entrada" removed; components placed directly in tab)
                classification = gr.Dropdown(
                    choices=["Pràctica 1. Revista", "Pràctica 2. Xarxes Socials"],
                    label="📋 Classificació d'Imatges",
                    show_label=False,
                    value=None,
                    info="¿Quina pràctica vols analitzar?",
                    elem_classes=["visible-dropdown", "with-info", "larger-font"],
                )
                with gr.Row():
                    with gr.Column(scale=4):
                        files = gr.File(
                            file_count="multiple",
                            file_types=["image"],
                            label=f"📸 Afegir imatges",
                            height=200,
                            elem_id="file-uploader",
                            elem_classes=["large-upload-button"],
                        )
                    # with gr.Column(scale=1):
                    #     image_counter = gr.Markdown(
                    #         value=f"**Imatges**: 0/{MAX_IMAGES}", visible=True
                    #     )

                rows, thumbnail_images, type_dropdowns = [], [], []
                for i in range(0, MAX_IMAGES, 2):
                    with gr.Row(visible=False) as row:
                        rows.append(row)
                        with gr.Column(scale=1, min_width=360):
                            with gr.Row(elem_classes=["thumbline"]):  # ⬅️ add thumbline
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
                                with gr.Column(scale=1, min_width=180, elem_classes=["vcenter-col"]):  # ⬅️ add vcenter-col
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
                        with gr.Column(scale=1, min_width=360):
                            with gr.Row(elem_classes=["thumbline"]):  # ⬅️ add thumbline
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
                                with gr.Column(scale=1, min_width=180, elem_classes=["vcenter-col"]):  # ⬅️ add vcenter-col
                                    dd_b = gr.Dropdown(
                                        choices=[],
                                        label=f"Tipus per a Imatge {i + 2}",
                                        value=None,
                                        visible=False,
                                        elem_classes=["visible-dropdown", "medium-font"],
                                        allow_custom_value=True,
                                        show_label=False,
                                    )
                            thumbnail_images.append(thumb_b)
                            type_dropdowns.append(dd_b)

                user_description = gr.Textbox(
                    label="📝 Descripció",
                    placeholder="Descriviu què heu fet o qualsevol context addicional sobre aquestes imatges…",
                    lines=3,
                    max_lines=5,
                    show_label=False,
                    info="Descripció",
                    elem_classes=["emphasized-input", "with-info", "larger-font"],
                )
                status_message = gr.Markdown(
                    value="🧑‍🎓 **Estat**: Introduïu el vostre identificador d'estudiant per començar",
                    visible=True,
                    elem_classes=["status-message", "larger-font"],
                )
                analyze_btn = gr.Button(
                    "🔍 Analitzar",
                    variant="primary",
                    interactive=False,
                    size="lg",
                    elem_classes=["purple-button"],
                )

                gr.Markdown(
                    "## 🤖 Resultats de l'Anàlisi IA", elem_classes=["analysis-section"]
                )
                llm_output = gr.Markdown(
                    value="Pugeu imatges, seleccioneu classificació i cliqueu '🔍 Analitzar Imatges'...",
                    elem_classes=["analysis-section", "llm-output"],
                )

            # ----- Tab: Conversa -----
            with gr.TabItem("Anàlisi"):
                gr.Markdown("## 💬 Conversa amb l'Assistent IA")
                chat = gr.Chatbot(
                    type="messages",
                    label="Sessió de tutoria",
                    height=600,
                    elem_classes=["chatbot-surface"],
                )
                composer = gr.MultimodalTextbox(
                    placeholder="Escriu un missatge o adjunta imatges…",
                    file_count="multiple",
                    file_types=["image"],
                    show_label=False,
                    interactive=False,
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
                id_accordion,
                tabs_wrapper,
                composer,
                active_user_id,
                chat,
                user_id_input,
                confirm_id_btn,
                id_content,
            ],
        )
        user_id_input.submit(
            fn=commit_id,
            inputs=[user_id_input],
            outputs=[
                id_accordion,
                tabs_wrapper,
                composer,
                active_user_id,
                chat,
                user_id_input,
                confirm_id_btn,
                id_content,
            ],
        )

        # all_outputs = [image_counter] + rows + thumbnail_images + type_dropdowns
        all_outputs = rows + thumbnail_images + type_dropdowns

        # 1) CLASSIFICATION change: update UI, then recompute status
        classification.change(
            fn=update_type_dropdowns,
            inputs=[files, classification],
            outputs=all_outputs,
        ).then(
            fn=update_button_and_status,
            inputs=[active_user_id, files, classification, user_description]
            + type_dropdowns,
            outputs=[analyze_btn, status_message],
        )

        # 2) FILES change (upload/delete): update UI, then recompute status
        files.change(
            fn=update_type_dropdowns,
            inputs=[files, classification],
            outputs=all_outputs,
        ).then(
            fn=update_button_and_status,
            inputs=[active_user_id, files, classification, user_description]
            + type_dropdowns,
            outputs=[analyze_btn, status_message],
        )

        for component in [files, classification, user_description] + type_dropdowns:
            component.change(
                fn=update_button_and_status,
                inputs=[active_user_id, files, classification, user_description]
                + type_dropdowns,
                outputs=[analyze_btn, status_message],
            )

        # No more input_accordion in outputs
        analyze_btn.click(
            fn=analyze_and_close,
            inputs=[active_user_id, files, classification, user_description]
            + type_dropdowns,
            outputs=[llm_output, chat],
        )

    demo.launch(debug=True)


if __name__ == "__main__":
    main()
