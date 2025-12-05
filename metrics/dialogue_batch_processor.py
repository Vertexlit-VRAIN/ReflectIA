import os
import sys
import time
import glob
import google.generativeai as genai

# ==========================================
# CONFIGURATION
# ==========================================

# PASTE YOUR API KEY HERE
API_KEY = ""

# Model configuration
MODEL_NAME = "gemini-2.5-pro"

# Folder Names
INPUT_DIR = "inputs"
OUTPUT_DIR = "outputs"
PROMPT_DIR = "prompts"

# Error Handling Settings
RETRY_DELAY = 30  # Seconds to wait before retrying
MAX_RETRIES = 2   # Number of retries before killing connection

# ==========================================
# FUNCTIONS
# ==========================================

def setup_environment():
    """Checks folders and configures API."""
    if not os.path.exists(PROMPT_DIR):
        print(f"ERROR: '{PROMPT_DIR}' folder not found. Please create it and add prompt text files.")
        sys.exit(1)
        
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created '{INPUT_DIR}'. Please put your .txt dialogue files here.")
        sys.exit(0)

    genai.configure(api_key=API_KEY)
    return genai.GenerativeModel(MODEL_NAME)

def load_prompts():
    """Reads all .txt files from the prompts folder."""
    prompts = {}
    files = glob.glob(os.path.join(PROMPT_DIR, "*.txt"))
    
    if not files:
        print(f"ERROR: No .txt files found in '{PROMPT_DIR}'.")
        sys.exit(1)

    for p_file in files:
        # Filename becomes the task name (e.g., 'feedback.txt' -> 'feedback')
        task_name = os.path.splitext(os.path.basename(p_file))[0]
        with open(p_file, 'r', encoding='utf-8') as f:
            prompts[task_name] = f.read()
            
    return prompts

def analyze_file(model, task_name, prompt_template, dialogue_path):
    """Runs the API call with retry logic and caching."""
    
    file_name = os.path.basename(dialogue_path)
    
    # create specific output folder for this task (e.g., outputs/feedback/)
    task_output_dir = os.path.join(OUTPUT_DIR, task_name)
    if not os.path.exists(task_output_dir):
        os.makedirs(task_output_dir)

    output_file_path = os.path.join(task_output_dir, file_name)

    # 1. CHECK IF ALREADY DONE
    if os.path.exists(output_file_path):
        print(f"   [SKIP] {task_name} already exists for {file_name}")
        return

    # 2. PREPARE DATA
    try:
        with open(dialogue_path, 'r', encoding='utf-8') as f:
            dialogue_text = f.read()
    except Exception as e:
        print(f"   [ERROR] Could not read input file: {e}")
        return

    # Inject dialogue into the prompt template
    final_prompt = prompt_template.replace("{TEXT}", dialogue_text)

    # 3. API EXECUTION WITH RETRY
    attempts = 0
    while attempts <= MAX_RETRIES:
        try:
            print(f"   [RUN] Processing {task_name} (Attempt {attempts + 1})...")
            
            response = model.generate_content(final_prompt)
            
            # Save result
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Small pause to be nice to the API
            time.sleep(1)
            return

        except Exception as e:
            print(f"   [FAIL] API Error: {e}")
            attempts += 1
            
            if attempts <= MAX_RETRIES:
                print(f"   [WAIT] Cooling down for {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("   [CRITICAL] Max retries reached. Stopping script safely.")
                sys.exit(1) # Terminates the entire script

# ==========================================
# MAIN LOOP
# ==========================================

def main():
    print("--- Dialogue Analysis Started ---")
    
    model = setup_environment()
    prompts = load_prompts()
    dialogue_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.txt")))

    if not dialogue_files:
        print(f"No files found in '{INPUT_DIR}'.")
        return

    print(f"Loaded {len(prompts)} prompts types: {list(prompts.keys())}")
    print(f"Found {len(dialogue_files)} dialogues to process.\n")

    for d_file in dialogue_files:
        print(f"📂 FILE: {os.path.basename(d_file)}")
        
        for task_name, prompt_text in prompts.items():
            analyze_file(model, task_name, prompt_text, d_file)
        print("-" * 40)

    print("--- All Processing Complete ---")

if __name__ == "__main__":
    main()
