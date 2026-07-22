import os
import sys
from google import genai
from google.genai import types

# --- Agent Tools ---

def write_file(filepath: str, content: str) -> str:
    """Creates or overwrites a file in the repository with the specified content."""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Agent Tool] File written: {filepath}")
    return f"File '{filepath}' saved successfully."

def read_file(filepath: str) -> str:
    """Reads the content of an existing file in the repository."""
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' does not exist."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def list_files(directory: str = ".") -> str:
    """Lists all files in the repository, excluding build and version control directories."""
    files = []
    for root, _, filenames in os.walk(directory):
        if any(ignored in root for ignored in [".git", "__pycache__", ".venv", ".github", "node_modules"]):
            continue
        for fn in filenames:
            files.append(os.path.relpath(os.path.join(root, fn), directory))
    return "\n".join(files) if files else "No files found."


def main():
    project_id = os.environ.get("GCP_PROJECT_ID")
    location = os.environ.get("GCP_LOCATION", "europe-west3") # z.B. europe-west3 oder us-central1
    prompt = os.environ.get("AGENT_PROMPT")

    if not prompt and len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])

    if not prompt:
        prompt = "Set up the basic project structure and configuration for the 'plotikz' package."

    print("--- Starting Gemini Agent (google.genai) ---")

    # Client für Vertex AI
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )

    config = types.GenerateContentConfig(
        system_instruction=(
            "You are an autonomous software developer working on the Python package 'plotikz'. "
            "Use the 'write_file' tool to write generated code and files directly to the repository. "
            "Use 'list_files' and 'read_file' to examine existing code and understand project context before making changes."
        ),
        tools=[write_file, read_file, list_files],
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=2048)
    )

    chat = client.chats.create(model="gemini-3.6-flash", config=config)
    response = chat.send_message(prompt)

    print("\n--- Agent Response ---")
    print(response.text)

if __name__ == "__main__":
    main()
