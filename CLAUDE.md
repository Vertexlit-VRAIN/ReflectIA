# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RosoUX is a Gradio-based AI image analysis application that provides detailed feedback on editorial and social network content. The application currently uses Ollama for local LLM inference (specifically the `llava-phi3:latest` model) but will be migrated to API calls in the future.

## Technology Stack

- **Python**: 3.13+
- **Package Manager**: UV (modern Python package manager)
- **Web Framework**: Gradio 5.39.0+ for the web interface
- **AI/ML**: Currently Ollama (local) with llava-phi3:latest model
- **Language**: Catalan UI with multilingual support

## Development Commands

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependencies
uv add package_name

# Remove dependencies
uv remove package_name

# Run the application
uv run python main.py

# Run with Gradio sharing enabled
uv run python main.py  # Edit main.py to use demo.launch(share=True)

# Run markdown test interface
uv run python test_markdown.py
```

### Development Workflow
```bash
# Update lockfile
uv lock

# Export dependencies to requirements.txt format (if needed)
uv export --format requirements-txt --output-file requirements.txt
```

## Application Architecture

### Core Structure
```
main.py              # Main Gradio application entry point
test_markdown.py     # Testing interface for markdown rendering
src/                 # Planned modular architecture (currently empty)
├── api/            # Future API integration modules
├── core/           # Core business logic
├── ui/             # UI components and layouts
└── utils/          # Utility functions
static/             # Static assets
config/             # Configuration files (currently empty)
```

### Key Components (main.py)

**Image Processing Pipeline:**
- `encode_image_to_base64()`: Converts images to base64 for Ollama API
- `call_ollama_model()`: Handles communication with local Ollama instance
- `generate_llm_response()`: Main orchestration function for analysis

**UI Management:**
- `update_type_dropdowns()`: Dynamic form management for up to 10 images
- `auto_detect_image_type()`: Intelligent type detection based on filenames
- `check_button_state()` / `update_status_message()`: Form validation and UX

**Content Types:**
- **Editorial**: portada (cover), interior
- **Social Network**: instagram artista, instagram concurs, twitter artista

### Key Features
- Multi-image upload (up to 10 images)
- Dynamic type detection based on filename patterns
- Catalan language interface
- Progress tracking during analysis
- Mobile-responsive design with custom CSS
- Real-time form validation

## Important Implementation Notes

### Ollama Integration (Temporary)
The application currently connects to a local Ollama instance at `http://localhost:11434/api/generate` using the `llava-phi3:latest` model. This will be replaced with API calls in future versions.

**Current Ollama setup requirements:**
- Ollama server running locally
- `llava-phi3:latest` model installed
- Connection timeout set to 60 seconds

### Image Type Auto-Detection Logic
The system automatically detects image types based on filename patterns:
- Editorial: "cover/portada/front" → portada, "inside/interior/page" → interior
- Social Network: "instagram" + "contest/concurs" → instagram concurs, "twitter" → twitter artista

### Form Validation Flow
The application requires all fields to be completed before analysis:
1. Classification selection (Editorial/Social Network)
2. Image upload (1-10 images)
3. Type specification for each image
4. User description text

### UI/UX Considerations
- Purple theme (#611DD9) for primary actions
- Mobile-first responsive design
- Accessibility features (focus outlines, proper ARIA labels)
- Real-time status updates and progress tracking
- Error handling with user-friendly Catalan messages

## Future Architecture Plans

The `src/` directory structure suggests a planned modularization:
- Move image processing logic to `src/core/`
- Extract UI components to `src/ui/`
- Create API abstraction in `src/api/`
- Add utility functions to `src/utils/`
- Configuration management in `config/`