import gradio as gr


def generate_llm_response(files, classification, *type_selections):
    if not files:
        return "Please upload at least one image for analysis."

    if not classification:
        return "Please select a classification first."

    # Filter out None values and check if we have type selections for all images
    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]
    if len(valid_types) != len(files):
        return f"Please specify the type for all {len(files)} uploaded images."

    analysis_results = []

    for i, image_type in enumerate(valid_types):
        filename = files[i].name if hasattr(files[i], "name") else f"Image {i + 1}"
        if classification == "Editorial":
            analysis_results.append(f"""
**{filename}** - {image_type}:
• Professional editorial {image_type.lower()} with excellent visual hierarchy
• Brand alignment suitable for {image_type.lower()} placement
• Meets editorial standards for publication
""")
        else:  # Social Network
            analysis_results.append(f"""
**{filename}** - {image_type}:
• Optimized for {image_type.lower()} social media format
• High engagement potential for {image_type.lower()} posts
• Suitable for social platform audience
""")

    header = f"✨ **{classification} Analysis Complete**\n"
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
        type_options = ["cover", "interior"]
    elif classification == "Social Network":
        type_options = ["instagram artiste", "instagram concurs", "twiter artista"]

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
            dropdown_updates.append(
                gr.update(
                    visible=True,
                    choices=type_options,
                    value=None,
                    label=f"Type for {files[i].name if hasattr(files[i], 'name') else f'Image {i + 1}'}",
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


def check_button_state(files, classification, *type_selections):
    if not files or not classification:
        return gr.update(interactive=False)

    # Check if all uploaded images have type selections
    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]
    return gr.update(interactive=len(valid_types) == len(files))


with gr.Blocks(title="RosoUX - AI Image Analysis") as demo:
    gr.Markdown("# 🎨 RosoUX Image Analysis")
    gr.Markdown(
        "### Upload your images and discover AI-powered insights for editorial and social media content"
    )

    # Image classification selection
    classification = gr.Dropdown(
        choices=["Editorial", "Social Network"],
        label="📋 Image Classification",
        value=None,
    )

    # File upload
    files = gr.File(
        file_count="multiple",
        file_types=["image"],
        label="📸 Upload Images",
        height=150,
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
                    label=f"Type for Image {i + 1}",
                    visible=False,
                    value=None,
                )
                type_dropdowns.append(dropdown)

    analyze_btn = gr.Button(
        "🔍 Analyze Images", variant="primary", interactive=False, size="lg"
    )

    # Bottom section - LLM response
    gr.Markdown("## 🤖 AI Analysis Results")
    llm_output = gr.Textbox(
        label="📊 Detailed Analysis",
        lines=15,
        placeholder="Upload images, select classification, specify type for each image, then click '🔍 Analyze Images'...",
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
    all_inputs = [files, classification] + type_dropdowns

    for component in all_inputs:
        component.change(
            fn=check_button_state,
            inputs=all_inputs,
            outputs=[analyze_btn],
        )

    analyze_btn.click(
        fn=generate_llm_response,
        inputs=[files, classification] + type_dropdowns,
        outputs=llm_output,
    )

demo.launch()
