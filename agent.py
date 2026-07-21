import os
import sys
import google.generativeai as genai

def main():
    # 1. API-Key aus Umgebungsvariable laden
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Fehler: GEMINI_API_KEY wurde nicht gefunden!", file=sys.stderr)
        sys.exit(1)

    # 2. Prompt aus Umgebungsvariable oder Argumenten laden
    prompt = os.environ.get("AGENT_PROMPT")
    if not prompt and len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])

    if not prompt:
        print("Fehler: Kein AGENT_PROMPT übergeben!", file=sys.stderr)
        sys.exit(1)

    print("--- Gemini Agent gestartet ---")
    
    # 3. Gemini SDK konfigurieren & Modell aufrufen
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")

    # 4. Antwort generieren
    response = model.generate_content(prompt)

    print("\n--- Antwort von Gemini ---")
    print(response.text)

if __name__ == "__main__":
    main()
