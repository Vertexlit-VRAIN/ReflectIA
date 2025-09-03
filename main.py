"""
Main application for AI Image Analysis.

This script launches a Gradio interface for analyzing images based on different
classifications (e.g., Editorial, Social Network).
"""

import gradio as gr

from config import MAX_IMAGES
from gradio_callbacks import (
    generate_llm_response,
    update_button_and_status,
    update_type_dropdowns,
)


# --- Gradio Interface ---
def main():
    """Launches the Gradio interface for the application."""
    with open("static/styles.css", "r", encoding="utf-8") as f:
        custom_css = f.read()

    with gr.Blocks(
        title="AI Image Analysis",
        theme="Taithrah/Minimal",
        css=custom_css,
    ) as demo:
        gr.Markdown("# Anàlisi d'Imatges")
        gr.Markdown(
            "### Pugeu les vostres imatges i descobriu informació potenciada per IA per a contingut editorial i de xarxes socials"
        )

        with gr.Tabs(elem_classes=["main-tabs"]):
            with gr.TabItem("Anàlisi"):
                # Accordion (we will close it on analyze)
                with gr.Accordion("Entrada", open=True) as input_accordion:
                    user_id = gr.Textbox(
                        label="🧑‍🎓 Identificador d'Estudiant",
                        placeholder="Introduïu el vostre identificador únic...",
                        info="💡 Aquest identificador s'utilitzarà per desar i recuperar les vostres converses.",
                        elem_classes=["emphasized-input", "with-info"],
                    )

                    # Image classification
                    classification = gr.Dropdown(
                        choices=["Editorial", "Social Network"],
                        label="📋 Classificació d'Imatges",
                        value=None,
                        elem_classes=["visible-dropdown", "with-info"],
                        info="💡 Trieu 'Editorial' per revistes/llibres o 'Social Network' per contingut de xarxes socials",
                    )

                    # File upload + counter
                    with gr.Row():
                        with gr.Column(scale=4):
                            files = gr.File(
                                file_count="multiple",
                                file_types=["image"],
                                label=f"📸 Afegir imatges (màxim {MAX_IMAGES})",
                                height=200,
                                elem_classes="large-upload-button",
                            )
                        with gr.Column(scale=1):
                            image_counter = gr.Markdown(
                                value=f"**Imatges**: 0/{MAX_IMAGES}", visible=True
                            )

                    # ---------- PURE GRADIO LAYOUT: 2 COLUMNS ----------
                    # Pre-create ceil(MAX_IMAGES/2) rows; each row has 2 slots.
                    # Each slot = [thumbnail | dropdown] in two inner columns.
                    rows = []
                    thumbnail_images = []
                    type_dropdowns = []

                    for i in range(0, MAX_IMAGES, 2):
                        with gr.Row(visible=False) as row:
                            rows.append(row)

                            # SLOT A (left)
                            with gr.Column(scale=1, min_width=360):
                                with gr.Row():
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
                                    with gr.Column(scale=1, min_width=180):
                                        dd_a = gr.Dropdown(
                                            choices=[],
                                            label=f"Tipus per a Imatge {i + 1}",
                                            value=None,
                                            visible=False,
                                            elem_classes=["visible-dropdown"],
                                        )
                                thumbnail_images.append(thumb_a)
                                type_dropdowns.append(dd_a)

                            # SLOT B (right) — only if exists
                            with gr.Column(scale=1, min_width=360):
                                with gr.Row():
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
                                    with gr.Column(scale=1, min_width=180):
                                        dd_b = gr.Dropdown(
                                            choices=[],
                                            label=f"Tipus per a Imatge {i + 2}",
                                            value=None,
                                            visible=False,
                                            elem_classes=["visible-dropdown"],
                                        )
                                thumbnail_images.append(thumb_b)
                                type_dropdowns.append(dd_b)

                    # Description
                    user_description = gr.Textbox(
                        label="📝 Descripció",
                        placeholder=(
                            "Descriviu què heu fet o qualsevol context addicional sobre aquestes imatges...\n"
                            "Exemple: 'Disseny per la campanya de primavera 2024' o 'Post promocional per a Instagram'"
                        ),
                        lines=3,
                        max_lines=5,
                        info="💡 Descripció requerida per analitzar les imatges",
                        elem_classes=["emphasized-input", "with-info"],
                    )

                    # Status & button
                    status_message = gr.Markdown(
                        value="🧑‍🎓 **Estat**: Introduïu el vostre identificador d'estudiant per començar",
                        visible=True,
                        elem_classes=["status-message"],
                    )

                    analyze_btn = gr.Button(
                        "🔍 Analitzar Imatges",
                        variant="primary",
                        interactive=False,
                        size="lg",
                        elem_classes=["purple-button"],
                    )

                # Results
                gr.Markdown("## 🤖 Resultats de l'Anàlisi IA", elem_classes=["analysis-section"])
                llm_output = gr.Markdown(
                    value=(
                        "Pugeu imatges, seleccioneu classificació, especifiqueu el tipus per a cada imatge "
                        "i després cliqueu '🔍 Analitzar Imatges'..."
                    ),
                    elem_classes=["analysis-section", "llm-output"],
                )

            with gr.TabItem("Conversa"):
                gr.Markdown("## 💬 Conversa amb l'Assistent IA")
                gr.Markdown("Properament...")

        # -------- Wire events --------
        # Order of outputs must match update_type_dropdowns return:
        # [counter] + rows + thumbnails + dropdowns
        all_outputs = [image_counter] + rows + thumbnail_images + type_dropdowns

        classification.change(
            fn=update_type_dropdowns,
            inputs=[files, classification],
            outputs=all_outputs,
        )
        files.change(
            fn=update_type_dropdowns,
            inputs=[files, classification],
            outputs=all_outputs,
        )

        # Enable button + live status
        for component in [user_id, files, classification, user_description] + type_dropdowns:
            component.change(
                fn=update_button_and_status,
                inputs=[user_id, files, classification, user_description] + type_dropdowns,
                outputs=[analyze_btn, status_message],
            )

        # Click: run analysis AND close the accordion
        def analyze_and_close(
            user_id, files, classification, user_description, *type_selections
        ):
            text = generate_llm_response(
                user_id, files, classification, user_description, *type_selections
            )
            return text, gr.update(open=False)

        analyze_btn.click(
            fn=analyze_and_close,
            inputs=[user_id, files, classification, user_description] + type_dropdowns,
            outputs=[llm_output, input_accordion],
        )

    demo.launch(debug=True)


if __name__ == "__main__":
    main()
