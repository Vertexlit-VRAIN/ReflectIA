# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- `uv sync` - Install/update dependencies
- `uv run main.py` - Start the Gradio application

### Package Management  
- `uv add <package>` - Add new dependency
- `uv remove <package>` - Remove dependency

## Architecture

CritiCat is an AI-powered image analysis tool built with Python and Gradio. It provides detailed feedback for different types of visual content (editorial, social media, etc.).

### Core Components

**main.py** - Application entry point with Gradio interface setup. Handles user ID management and tab visibility logic.

**gradio_callbacks.py** - Event handlers for UI interactions. Contains `generate_llm_response()` for image analysis and conversation handling.

**ai_providers.py** - AI model integration layer supporting both Gemini (`call_gemini_model()`) and Ollama (`call_ollama_model()`). Handles multimodal requests with image encoding.

**config.py** - Configuration management with environment variables. Controls AI provider selection (`AI_PROVIDER`), model settings, and debug modes.

**history_manager.py** - Conversation persistence using JSON files in `messages/` directory, keyed by user ID.

**image_utils.py** - Image processing utilities for base64 encoding and format conversion.

### Prompt System

The `prompts/` directory contains specialized analysis templates:
- `prompt_design.txt` - General visual design analysis  
- `prompt_magazine.txt` / `prompt_magazine_full.txt` - Editorial content analysis
- `prompt_social.txt` / `prompt_social_full.txt` - Social media post analysis
- `prompt_conversation.txt` - Conversational tutoring mode

### Key Patterns

- User sessions identified by text ID input, persisted in `messages/<uid>.json`
- Dual-mode UI: image analysis tab + conversation tab
- AI provider abstraction allows switching between Gemini and Ollama
- Gradio component state management through update functions
- Multimodal conversation history with image support

### Environment Setup

Requires `GOOGLE_API_KEY` environment variable for Gemini API access. Optional `OLLAMA_URL` and `OLLAMA_MODEL` for local Ollama setup.