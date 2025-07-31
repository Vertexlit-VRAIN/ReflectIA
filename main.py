import base64
import json

import gradio as gr
import requests


def encode_image_to_base64(image_path):
    """Convert image to base64 string for Ollama"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        return None


def call_ollama_model(prompt, images_base64=None):
    """Call local Ollama model"""
    try:
        url = "http://localhost:11434/api/generate"

        payload = {"model": "llava-phi3:latest", "prompt": prompt, "stream": False}

        # Add images if provided
        if images_base64:
            payload["images"] = images_base64

        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response from model")
        else:
            return f"Error: Ollama returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return "Error: No s'ha pogut connectar amb Ollama. Assegureu-vos que Ollama està funcionant a localhost:11434"
    except requests.exceptions.Timeout:
        return "Error: Timeout - El model ha trigat massa temps a respondre"
    except Exception as e:
        return f"Error: {str(e)}"


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

    # Prepare images for Ollama
    images_base64 = []
    image_info = []

    for i, file in enumerate(files):
        if hasattr(file, "name"):
            image_path = file.name
        else:
            image_path = str(file)

        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        if base64_image:
            images_base64.append(base64_image)
            filename = (
                image_path.split("/")[-1] if "/" in image_path else f"Image {i + 1}"
            )
            image_info.append(f"{filename} - {valid_types[i]}")

    # Create prompt for Ollama
    context = f"Classificació: {classification}\n"
    if user_description and user_description.strip():
        context += f"Descripció de l'usuari: {user_description.strip()}\n"

    context += f"Imatges a analitzar: {', '.join(image_info)}\n"

    prompt = f"""
{context}

Analitza aquestes imatges segons la classificació '{classification}' i proporciona una anàlisi detallada en català.

Per a cada imatge, proporciona:
- Una avaluació de la qualitat visual
- Adequació per al tipus especificat ({", ".join(set(valid_types))})
- Recomanacions específiques

Respon en format markdown amb punts clars i concisos.
"""

    # Call Ollama model
    return call_ollama_model(prompt, images_base64)


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


with gr.Blocks(
    title="RosoUX - AI Image Analysis",
    theme="Taithrah/Minimal",
    css="""
    /* Light gray background only for dropdown input field */
    .visible-dropdown select,
    .visible-dropdown input,
    .visible-dropdown .gr-box,
    .visible-dropdown .wrap {
        background-color: #3b3b3b !important;
        color: white !important;
    }
    
    /* Change textbox focus background to 3b3b3b */
    textarea:focus {
        background-color: #3b3b3b !important;
    }
    
    /* Change analyze button color */
    .purple-button,
    button[variant="primary"],
    .gr-button-primary,
    button.primary {
        background-color: #611DD9 !important;
        border-color: #611DD9 !important;
        background: #611DD9 !important;
    }
    
    .purple-button:hover,
    button[variant="primary"]:hover,
    .gr-button-primary:hover,
    button.primary:hover {
        background-color: #5016b3 !important;
        border-color: #5016b3 !important;
        background: #5016b3 !important;
    }
    """,
) as demo:
    gr.Markdown("# 🎨 RosoUX Anàlisi d'Imatges")
    gr.Markdown(
        "### Pugeu les vostres imatges i descobriu informació potenciada per IA per a contingut editorial i de xarxes socials"
    )

    # Image classification selection
    classification = gr.Dropdown(
        choices=["Editorial", "Social Network"],
        label="📋 Classificació d'Imatges",
        value=None,
        elem_classes=["visible-dropdown"],
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
                    elem_classes=["visible-dropdown"],
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
        "🔍 Analitzar Imatges",
        variant="primary",
        interactive=False,
        size="lg",
        elem_classes=["purple-button"],
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

demo.launch(share=True)
