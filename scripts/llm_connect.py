"""
llm_connect.py  --  Piece 1: prove the AI connections work.

This does ONE thing: it sends a tiny message to each model and prints the reply.
No questions, no learner model -- just "can we talk to the model?".

Keys are read from ENVIRONMENT VARIABLES (never typed into this file):
    GROQ_API_KEY    -> our GENERATOR (writes the questions)
    GROQ_MODEL      -> optional model override; otherwise an accessible model is selected
    GEMINI_API_KEY  -> our VERIFIER  (checks the questions)
    GEMINI_MODEL    -> optional Gemini model override

--- Windows setup (Command Prompt) ---
    set GROQ_API_KEY=your_key_here
    set GEMINI_API_KEY=your_key_here

--- Windows setup (PowerShell) ---
    $env:GROQ_API_KEY="your_key_here"
    # Optional: force a specific model returned by Groq's model list.
    $env:GROQ_MODEL="llama-3.1-8b-instant"
    $env:GEMINI_API_KEY="your_key_here"
    # Optional: override the current Gemini model.
    $env:GEMINI_MODEL="gemini-3.8-flash"

--- Install the two packages ---
    pip install groq google-genai

--- Run ---
    python llm_connect.py
"""

import os

# Groq model availability depends on the account and changes over time. The
# optional GROQ_MODEL environment variable takes precedence.
GROQ_MODEL = os.environ.get("GROQ_MODEL")
GROQ_MODEL_PREFERENCES = (
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
)
# Gemini model names are retired periodically. Keep this configurable so the
# provider's current model can be selected without editing the script.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
AI_REQUEST_TIMEOUT_SECONDS = 30


def test_groq():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        print("  GROQ_API_KEY is not set -- skipping. (See the top of this file.)")
        return
    try:
        from groq import APIConnectionError, APIStatusError, Groq
    except ImportError:
        print("  The 'groq' package is missing. Run:  pip install groq")
        return
    client = Groq(api_key=key)
    try:
        available_models = {model.id for model in client.models.list().data}
        if GROQ_MODEL:
            if GROQ_MODEL not in available_models:
                print(
                    f"  GROQ_MODEL={GROQ_MODEL!r} is not available for this key. "
                    "Choose one of the models returned by Groq."
                )
                return
            model_name = GROQ_MODEL
        else:
            model_name = next(
                (
                    model
                    for model in GROQ_MODEL_PREFERENCES
                    if model in available_models
                ),
                None,
            )
            if model_name is None:
                print(
                    "  No supported text model is available for this Groq key. "
                    "Set GROQ_MODEL to an accessible model ID."
                )
                return

        reply = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Reply with exactly: Groq connection OK"}],
            temperature=0,
        )
        print(f"  Groq ({model_name}) replied:", reply.choices[0].message.content.strip())
    except (APIStatusError, APIConnectionError) as error:
        print("  Groq call failed:", error)


def test_gemini():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("  GEMINI_API_KEY is not set -- skipping. (See the top of this file.)")
        return

    # Try the newer SDK first, then fall back to the older one.
    try:
        from google import genai as new_genai
        from google.genai import types

        client = new_genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=AI_REQUEST_TIMEOUT_SECONDS * 1000
            ),
        )
        reply = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Reply with exactly: Gemini connection OK",
        )
        text = (reply.text or "").strip()
        if not text:
            print("  Gemini returned an empty response.")
            return
        print("  Gemini replied:", text)
        return
    except ImportError:
        pass
    except Exception as e:
        print("  Gemini call failed:", e)
        return

    try:
        import google.generativeai as old_genai
        old_genai.configure(api_key=key)
        model = old_genai.GenerativeModel(GEMINI_MODEL)
        reply = model.generate_content(
            "Reply with exactly: Gemini connection OK",
            request_options={"timeout": AI_REQUEST_TIMEOUT_SECONDS},
        )
        text = (reply.text or "").strip()
        if not text:
            print("  Gemini returned an empty response.")
            return
        print("  Gemini replied:", text)
    except ImportError:
        print("  The Gemini package is missing. Run:  pip install google-genai")
    except Exception as e:
        print("  Gemini call failed:", e)


def main():
    print("Testing AI connections...")
    print("Groq  (our GENERATOR):")
    test_groq()
    print("Gemini (our VERIFIER):")
    test_gemini()
    print("Done. If both replied, we are ready for piece 2.")


if __name__ == "__main__":
    main()
