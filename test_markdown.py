import gradio as gr

def test_markdown_rendering():
    """Test function to verify markdown rendering works"""
    sample_markdown = """# 🎨 Test Analysis

**📋 Classification**: Editorial  
**📸 Images analyzed**: 2  

---

## Analysis Results

### Image 1: Cover Design
- **Quality**: Excellent visual composition
- **Adequacy**: Perfect for editorial cover
- **Recommendations**: 
  - Consider slight color adjustment
  - Increase contrast for better readability

### Image 2: Interior Layout
- **Quality**: Good layout structure
- **Adequacy**: Suitable for magazine interior
- **Recommendations**:
  - Add more white space
  - Improve typography hierarchy

---

## 📋 Image Summary
- **cover.jpg - portada**
- **interior.jpg - interior**
"""
    return sample_markdown

with gr.Blocks() as demo:
    gr.Markdown("# Markdown Rendering Test")
    
    test_btn = gr.Button("Test Markdown Rendering")
    
    result_display = gr.Markdown(
        value="Click the button to test markdown rendering...",
        elem_classes=["analysis-results"]
    )
    
    test_btn.click(
        fn=test_markdown_rendering,
        outputs=result_display
    )

if __name__ == "__main__":
    demo.launch(share=False, server_port=7861)