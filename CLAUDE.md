# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RosoUX is an AI-powered image analysis application built with Gradio that provides UX/UI feedback for editorial and social network content. The application uses a local Ollama model (gemma3:4b) to analyze uploaded images and provide detailed feedback in Catalan.

## Common Commands

### Development
```bash
# Run the main application
uv run python main.py

# Install dependencies (if needed)
uv sync  # or pip install gradio>=5.39.0
```

### Local Ollama Setup
The application requires Ollama running locally:
```bash
# Start Ollama service
ollama serve

# Pull the required model (if not installed)
ollama pull llava-phi3:latest
```

## Architecture

### Core Components

**main.py**: Primary application entry point containing:
- Gradio interface with multi-image upload (max 10 images)
- Dynamic UI that updates based on classification selection
- Image processing pipeline with base64 encoding and LRU caching
- Ollama API integration for vision-language analysis

**Key Functions**:
- `generate_llm_response()`: Main analysis pipeline (main.py:87-162)
- `encode_image_to_base64()`: Image preprocessing with caching (main.py:25-47)
- `call_ollama_model()`: Local model API integration (main.py:50-84)
- `update_type_dropdowns()`: Dynamic UI state management (main.py:165-223)
- `auto_detect_image_type()`: Intelligent type detection from filenames (main.py:226-251)

### UI Architecture

The interface uses a progressive disclosure pattern:
1. Classification selection (Editorial/Social Network)
2. Multi-image upload with counter
3. Dynamic thumbnail grid with type selectors
4. Auto-detection of image types based on filenames
5. Required user description field
6. Real-time validation and status updates

**Classification Types**:
- **Editorial**: "portada" (cover), "interior" (interior pages)
- **Social Network**: "Instagram Artista", "Instagram Concurs", "Twitter Artista", "Twitter Concurs", "Newsletter", "Logo", "Capçalera"

### Styling
- Custom CSS in `static/styles.css` with purple theme (#611DD9)
- Mobile-responsive design with accessibility features
- Dark mode elements for form inputs

### Configuration
- **Model**: llava-phi3:latest (Ollama)
- **API Endpoint**: http://localhost:11434/api/generate
- **Max Images**: 10 simultaneous uploads
- **Timeout**: 60 seconds for model responses
- **Theme**: "Taithrah/Minimal" with custom CSS overrides

### Error Handling
Comprehensive error handling for:
- Ollama connection issues with helpful troubleshooting
- File processing errors with specific feedback
- Model timeout scenarios
- Missing dependencies and configuration

### Caching Strategy
- LRU cache for base64 encoded images (maxsize=50)
- Cache key includes file size for invalidation on changes
- Reduces processing time for repeated image uploads

## Development Notes

### Testing
- `test_markdown.py` provides a standalone interface for testing Markdown rendering
- Runs on port 7861 to avoid conflicts with main app

### Localization
- All user-facing text is in Catalan
- Error messages include helpful troubleshooting steps in Catalan
- Interface labels and descriptions use Catalan terminology

### File Structure
- `static/styles.css`: Custom styling overrides
- `.gradio/`: Gradio-generated files (certificate.pem)