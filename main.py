import base64
from functools import lru_cache

import gradio as gr
import requests

# Constants
MAX_IMAGES = 10
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llava-phi3:latest"
TIMEOUT_SECONDS = 60


# Cache for base64 encoded images to avoid re-processing
@lru_cache(maxsize=50)
def cached_encode_image_to_base64(image_path, file_size):
    """Convert image to base64 string with caching"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        return None


def encode_image_to_base64(image_path):
    """Convert image to base64 string for Ollama with caching"""
    try:
        import os

        file_size = os.path.getsize(image_path)

        # Try cached version first
        cached_result = cached_encode_image_to_base64(image_path, file_size)
        if cached_result:
            return cached_result

        # Fallback to direct encoding if cache fails
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return {
            "error": f"❌ **Error**: No s'ha trobat el fitxer d'imatge: {image_path}"
        }
    except PermissionError:
        return {"error": f"❌ **Error**: No es tenen permisos per llegir: {image_path}"}
    except Exception as e:
        return {"error": f"❌ **Error**: No s'ha pogut processar la imatge: {str(e)}"}


def call_ollama_model(prompt, images_base64=None):
    """Call local Ollama model"""
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}

        # Add images if provided
        if images_base64:
            payload["images"] = images_base64

        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)

        if response.status_code == 200:
            result = response.json()
            return result.get(
                "response", "❌ **Error**: No s'ha rebut resposta del model"
            )
        else:
            return f"❌ **Error del Model**: Ollama ha retornat l'estat {response.status_code}\n\n🔧 **Solució**: Comproveu que el model '{OLLAMA_MODEL}' està instal·lat i disponible."

    except requests.exceptions.ConnectionError:
        return """❌ **Error de Connexió**: No s'ha pogut connectar amb Ollama

🔧 **Solucions possibles**:
- Assegureu-vos que Ollama està instal·lat i funcionant
- Executeu `ollama serve` al terminal
- Comproveu que el servei funciona a http://localhost:11434"""
    except requests.exceptions.Timeout:
        return """⏱️ **Error de Temps d'Espera**: El model ha trigat massa temps a respondre

🔧 **Solucions possibles**:
- Reduïu el nombre d'imatges
- Comproveu la connexió de xarxa
- Reinicieu el servei Ollama"""
    except Exception as e:
        return f"❌ **Error Inesperat**: {str(e)}\n\n🔧 **Solució**: Comproveu la configuració del sistema i torneu-ho a intentar."


def generate_llm_response(
    files, classification, user_description, *type_selections, progress=gr.Progress()
):
    progress(0, desc="Validant les dades d'entrada...")

    if not files:
        return "❌ **Error**: Si us plau, pugeu almenys una imatge per a l'anàlisi."

    if not classification:
        return "❌ **Error**: Si us plau, seleccioneu primer una classificació."

    # Filter out None values and check if we have type selections for all images
    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]
    if len(valid_types) != len(files):
        return f"❌ **Error**: Si us plau, especifiqueu el tipus per a totes les {len(files)} imatges pujades."

    progress(0.2, desc="Processant les imatges...")

    # Prepare images for Ollama
    images_base64 = []
    image_info = []

    for i, file in enumerate(files):
        progress(
            0.2 + (0.3 * i / len(files)),
            desc=f"Codificant imatge {i + 1} de {len(files)}...",
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

Respon amb punts clars i concisos.
"""

    progress(0.6, desc="Enviant petició al model d'IA...")

    # Call Ollama model
    result = call_ollama_model(prompt, images_base64)

    progress(1.0, desc="Anàlisi completada!")

    # Return simple result
    return format_analysis_results(result, classification, files, image_info)


def update_type_dropdowns(files, classification):
    image_count = len(files) if files else 0
    counter_text = f"**Imatges**: {image_count}/{MAX_IMAGES}"

    if not classification:
        # Return updates for counter, rows, images and dropdowns (31 total)
        return (
            [counter_text]
            + [gr.update(visible=False)] * 10
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
                return "instagram concurs"
            return "instagram artista"
        elif "twitter" in filename_lower:
            return "twitter artista"
        return "instagram artista"  # Default to Instagram artist

    return None


def update_button_and_status(files, classification, user_description, *type_selections):
    """Combined function to update both button state and status message"""
    # Common validation logic
    if not classification:
        return (
            gr.update(interactive=False),
            "📋 **Estat**: Seleccioneu primer una classificació (Editorial o Social Network)",
        )

    if not files:
        return (
            gr.update(interactive=False),
            "📸 **Estat**: Pugeu una o més imatges per analitzar",
        )

    valid_types = [
        t for t in type_selections[: len(files)] if t is not None and t != ""
    ]

    if len(valid_types) < len(files):
        missing_count = len(files) - len(valid_types)
        return (
            gr.update(interactive=False),
            f"🏷️ **Estat**: Especifiqueu el tipus per a {missing_count} imatge{'s' if missing_count > 1 else ''} més",
        )

    if not user_description or not user_description.strip():
        return (
            gr.update(interactive=False),
            "📝 **Estat**: Afegiu una descripció del vostre treball per continuar",
        )

    # All conditions met
    return (
        gr.update(interactive=True),
        f"✅ **Estat**: Tot preparat! {len(files)} imatge{'s' if len(files) > 1 else ''} {'preparades' if len(files) > 1 else 'preparada'} per analitzar",
    )


def format_analysis_results(result, classification, files, image_info):
    """Format the LLM results as plain text"""
    return result


with gr.Blocks(
    title="AI Image Analysis",
    theme="Taithrah/Minimal",
    css_paths=["static/styles.css"],
) as demo:
    gr.Markdown("# Anàlisi d'Imatges")
    gr.Markdown(
        "### Pugeu les vostres imatges i descobriu informació potenciada per IA per a contingut editorial i de xarxes socials"
    )

    # Image classification selection
    classification = gr.Dropdown(
        choices=["Editorial", "Social Network"],
        label="📋 Classificació d'Imatges",
        value=None,
        elem_classes=["visible-dropdown"],
        info="💡 Trieu 'Editorial' per revistes/llibres o 'Social Network' per contingut de xarxes socials",
    )

    # File upload with counter
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

    # Dynamic thumbnails and type selection dropdowns (up to 10 images)
    rows = []
    thumbnail_images = []
    type_dropdowns = []

    for i in range(MAX_IMAGES):
        row = gr.Row(visible=False)
        rows.append(row)

        with row:
            with gr.Column(scale=1):
                thumbnail = gr.Image(
                    type="filepath",
                    label=f"Image {i + 1}",
                    height=150,
                    width=150,
                    visible=False,
                    interactive=False,
                    show_label=False,
                    elem_classes=["thumbnail-container"],
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
        placeholder="Descriviu què heu fet o qualsevol context addicional sobre aquestes imatges...\nExemple: 'Disseny per la campanya de primavera 2024' o 'Post promocional per a Instagram'",
        lines=3,
        max_lines=5,
        info="💡 Descripció requerida per analitzar les imatges",
    )

    # Status indicator
    status_message = gr.Markdown(
        value="📋 **Estat**: Prepareu-vos per començar - seleccioneu una classificació i pugeu imatges",
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

    # Bottom section - LLM response
    gr.Markdown("## 🤖 Resultats de l'Anàlisi IA")
    llm_output = gr.Textbox(
        label="📊 Anàlisi Detallada",
        lines=15,
        placeholder="Pugeu imatges, seleccioneu classificació, especifiqueu el tipus per a cada imatge i després cliqueu '🔍 Analitzar Imatges'...",
        interactive=False,
        show_copy_button=True,
    )

    # Update thumbnails and type dropdowns when classification or files change
    def update_interface(files_input, classification_input):
        return update_type_dropdowns(files_input, classification_input)

    all_outputs = [image_counter] + rows + thumbnail_images + type_dropdowns

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

    # Update button state and status message when any input changes
    all_inputs = [files, classification, user_description] + type_dropdowns

    for component in all_inputs:
        component.change(
            fn=update_button_and_status,
            inputs=all_inputs,
            outputs=[analyze_btn, status_message],
        )

    analyze_btn.click(
        fn=generate_llm_response,
        inputs=[files, classification, user_description] + type_dropdowns,
        outputs=llm_output,
    )

# demo.launch(share=True)
demo.launch()
