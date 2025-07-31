import gradio as gr


def generate_llm_response(files, classification, user_description, *type_selections):
    if not files:
        return "Si us plau, pugeu almenys una imatge per a l'anàlisi."

    if not classification:
        return "Si us plau, seleccioneu primer una classificació."

    # Filter out None values and check if we have type selections for all images
    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]
    if len(valid_types) != len(files):
        return f"Si us plau, especifiqueu el tipus per a totes les {len(files)} imatges pujades."

    analysis_results = []

    # Add user description if provided
    if user_description and user_description.strip():
        analysis_results.append(
            f"**Descripció de l'Usuari:** {user_description.strip()}\n"
        )

    for i, image_type in enumerate(valid_types):
        filename = files[i].name if hasattr(files[i], "name") else f"Image {i + 1}"
        if classification == "Editorial":
            analysis_results.append(f"""
**{filename}** - {image_type}:
• {image_type.lower()} editorial professional amb excel·lent jerarquia visual
• Alineació de marca adequada per a col·locació de {image_type.lower()}
• Compleix els estàndards editorials per a publicació
""")
        else:  # Social Network
            analysis_results.append(f"""
**{filename}** - {image_type}:
• Optimitzat per al format de xarxes socials {image_type.lower()}
• Alt potencial d'engagement per a publicacions {image_type.lower()}
• Adequat per a l'audiència de plataformes socials
""")

    header = f"✨ **Anàlisi {classification} Completada**\n"
    return header + "\n".join(analysis_results)


def update_type_dropdowns(files, classification):
    if not classification:
        # Return updates for rows, images and dropdowns (30 total)
        return (
            [gr.update(visible=False)] * 10
            + [gr.update(visible=False, value=None)] * 10
            + [gr.update(visible=False, choices=[], value=None)] * 10
        )

    type_options = []
    if classification == "Editorial":
        type_options = ["portada", "interior"]
    elif classification == "Social Network":
        type_options = ["instagram artista", "instagram concurs", "twitter artista"]

    row_updates = []
    image_updates = []
    dropdown_updates = []

    if files:
        for i in range(len(files)):
            # Show row
            row_updates.append(gr.update(visible=True))
            # Show thumbnail image
            image_updates.append(gr.update(visible=True, value=files[i]))
            # Show dropdown with options
            filename = files[i].name if hasattr(files[i], "name") else f"Image {i + 1}"
            if "/" in filename:
                filename = filename.split("/")[-1]  # Get just the filename from path
            dropdown_updates.append(
                gr.update(
                    visible=True,
                    choices=type_options,
                    value=None,
                    label=f"Tipus per a {filename}",
                )
            )

        # Hide unused components
        for i in range(len(files), 10):
            row_updates.append(gr.update(visible=False))
            image_updates.append(gr.update(visible=False, value=None))
            dropdown_updates.append(gr.update(visible=False, choices=[], value=None))
    else:
        row_updates = [gr.update(visible=False)] * 10
        image_updates = [gr.update(visible=False, value=None)] * 10
        dropdown_updates = [gr.update(visible=False, choices=[], value=None)] * 10

    return row_updates + image_updates + dropdown_updates


def check_button_state(files, classification, user_description, *type_selections):
    if not files or not classification:
        return gr.update(interactive=False)

    # Check if user description is provided
    if not user_description or not user_description.strip():
        return gr.update(interactive=False)

    # Check if all uploaded images have type selections
    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]
    return gr.update(interactive=len(valid_types) == len(files))


with gr.Blocks(title="RosoUX - AI Image Analysis", theme="Taithrah/Minimal") as demo:
    gr.Markdown("# 🎨 RosoUX Anàlisi d'Imatges")
    gr.Markdown(
        "### Pugeu les vostres imatges i descobriu informació potenciada per IA per a contingut editorial i de xarxes socials"
    )

    # Image classification selection
    classification = gr.Dropdown(
        choices=["Editorial", "Social Network"],
        label="📋 Classificació d'Imatges",
        value=None,
    )

    # File upload
    files = gr.File(
        file_count="multiple",
        file_types=["image"],
        label="📸 Afegir imatges",
        height=200,
        elem_classes="large-upload-button",
    )

    # Dynamic thumbnails and type selection dropdowns (up to 10 images)
    rows = []
    thumbnail_images = []
    type_dropdowns = []

    for i in range(10):
        row = gr.Row(visible=False)
        rows.append(row)

        with row:
            with gr.Column(scale=1):
                thumbnail = gr.Image(
                    type="filepath",
                    label=f"Image {i + 1}",
                    height=100,
                    width=100,
                    visible=False,
                    interactive=False,
                    show_label=False,
                )
                thumbnail_images.append(thumbnail)

            with gr.Column(scale=2):
                dropdown = gr.Dropdown(
                    choices=[],
                    label=f"Tipus per a Imatge {i + 1}",
                    visible=False,
                    value=None,
                )
                type_dropdowns.append(dropdown)

    # User description text field
    user_description = gr.Textbox(
        label="📝 Descripció",
        placeholder="Descriviu què heu fet o qualsevol context addicional sobre aquestes imatges...",
        lines=3,
        max_lines=5,
    )

    analyze_btn = gr.Button(
        "🔍 Analitzar Imatges", variant="primary", interactive=False, size="lg"
    )

    # Bottom section - LLM response
    gr.Markdown("## 🤖 Resultats de l'Anàlisi IA")
    llm_output = gr.Textbox(
        label="📊 Anàlisi Detallada",
        lines=15,
        placeholder="Pugeu imatges, seleccioneu classificació, especifiqueu el tipus per a cada imatge, afegiu descripció i després cliqueu '🔍 Analitzar Imatges'...",
        interactive=False,
        show_copy_button=True,
    )

    # Update thumbnails and type dropdowns when classification or files change
    def update_interface(files_input, classification_input):
        return update_type_dropdowns(files_input, classification_input)

    all_outputs = rows + thumbnail_images + type_dropdowns

    classification.change(
        fn=update_interface,
        inputs=[files, classification],
        outputs=all_outputs,
    )

    files.change(
        fn=update_interface,
        inputs=[files, classification],
        outputs=all_outputs,
    )

    # Update button state when any input changes
    all_inputs = [files, classification, user_description] + type_dropdowns

    for component in all_inputs:
        component.change(
            fn=check_button_state,
            inputs=all_inputs,
            outputs=[analyze_btn],
        )

    analyze_btn.click(
        fn=generate_llm_response,
        inputs=[files, classification, user_description] + type_dropdowns,
        outputs=llm_output,
    )

demo.launch()
