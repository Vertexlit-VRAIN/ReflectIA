# ReflectIA

ReflectIA is an AI-assisted system for structured visual design feedback and conversational reflection in educational contexts.

The project combines multimodal large language models with structured prompting and a lightweight research pipeline for analyzing AI–student interactions.

---

## Overview

ReflectIA has two main components:

### 1. Interactive Application

- Upload and classify multiple images
- Generate individual image analyses
- Generate whole-project analysis
- Continue with reflective AI conversation
- Persistent per-student storage

The system is designed for design education scenarios where structured critique and iterative reflection are central.

### 2. Research Support

All interactions are stored in structured JSON format, enabling:

- Dialogue export
- Tag extraction
- Metric computation
- Quantitative and qualitative analysis

The repository includes scripts used in the ongoing research work.

---

## Current Prompt Versions

The system relies on structured prompts stored in the `prompts/` directory.

The current active prompts (as defined in `config.py`) are:

- `prompt_magazine_full_v5.txt`
- `prompt_social_full_v6.txt`
- `prompt_conversation_v5.4.txt`

These prompts define:

- Image-by-image analysis procedure
- Whole-project (conjunto) analysis structure
- Conversational tutoring behavior

All other prompts present in the repository correspond to earlier iterations and experimental versions.  
The current prompts are the result of progressive refinement and evolution across multiple design and research cycles.

---

## Installation

Requirements:

- Python 3.10.x
- `uv`

Install dependencies:

```bash
uv sync
```

---

## Configuration

Create a `.env` file in the project root:

```
GEMINI_API_KEY="your_api_key_here"
```

Or set it directly:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

AI provider configuration is defined in `config.py`.

Supported providers:

- Gemini (default)
- Ollama (local model)

---

## Running the Application

```bash
uv run main.py
```

This launches the Gradio interface in your browser.

---

## Data Storage

Each student has a dedicated folder:

```
data/<student_id>/
    messages.json
    state.json
    files/
```

All analyses and conversations are stored in JSON format for reproducibility and research purposes.

---

## Project Structure

```
ReflectIA/
├── main.py
├── ai_providers.py
├── gradio_callbacks.py
├── history_manager.py
├── compute_metrics.py
├── extract_generic.py
├── create_*.py
├── metrics/
├── prompts/
├── figures/
├── data/
└── static/
```

---

## Citation

A research paper describing ReflectIA is currently in preparation.

Until publication, please cite:

```bibtex
@misc{reflectia2026,
  author = {{Vertexlit-VRAIN}},
  title  = {{ReflectIA}: AI-Assisted Visual Design Feedback System},
  year   = {2026},
  note   = {GitHub repository. Related research paper in preparation.}
}
```
