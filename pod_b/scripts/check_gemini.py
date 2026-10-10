"""Verify your Gemini key end to end BEFORE building anything on it.

    python scripts/check_gemini.py

Reads GEMINI_API_KEY from the environment or .env. Never prints the key.
Checks: key accepted -> models available -> embeddings work -> JSON generation works.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from pod_b.config import Settings  # noqa: E402
from pod_b.embeddings import GeminiEmbedder  # noqa: E402
from pod_b.llm import GeminiLLM  # noqa: E402

s = Settings.from_env()
if not s.gemini_api_key:
    sys.exit("No GEMINI_API_KEY found. Put it in a .env file next to this project (see .env.example).")

HINTS = {
    400: "bad request - check the model name (set LLM_MODEL / EMBEDDING_MODEL to one listed above).",
    401: "key rejected - re-copy it, or create a new one in Google AI Studio.",
    403: "key valid but not allowed - check API restrictions on the key, or that the Generative Language API is enabled.",
    404: "model not found for this key - set LLM_MODEL / EMBEDDING_MODEL to a name from the list above.",
    429: "rate limit or quota - wait a minute, or check your plan; the pipeline retries with backoff automatically.",
}


def step(label, fn):
    try:
        out = fn()
        print(f"[PASS] {label}" + (f" - {out}" if out else ""))
        return True
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        code = next((c for c in HINTS if f"error {c}" in msg), None)
        print(f"[FAIL] {label}: {msg[:300]}")
        if code:
            print(f"       hint: {HINTS[code]}")
        return False


models = {}


def list_models():
    r = httpx.get(f"{GeminiLLM.BASE}/models", params={"pageSize": 200},
                  headers={"x-goog-api-key": s.gemini_api_key}, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"API error {r.status_code}: {r.text[:200]}")
    for m in r.json().get("models", []):
        models[m["name"].removeprefix("models/")] = set(m.get("supportedGenerationMethods", []))
    gen = sorted(n for n, ms in models.items() if "generateContent" in ms and "gemini" in n)
    emb = sorted(n for n, ms in models.items() if ms & {"embedContent", "batchEmbedContents"})
    print("       generation models:", ", ".join(gen[:12]) + (" ..." if len(gen) > 12 else ""))
    print("       embedding models  :", ", ".join(emb))
    return f"{len(models)} models visible"


ok = step("key accepted / list models", list_models)
llm_model = s.llm_model or GeminiLLM.DEFAULT_MODEL
emb_model = s.embedding_model if s.embedding_provider in ("gemini", "auto") and s.embedding_model else GeminiEmbedder.DEFAULT_MODEL
if ok:
    for label, name in (("LLM default model available", llm_model), ("embedding default model available", emb_model)):
        print(f"[{'PASS' if name in models else 'WARN'}] {label}: {name}" +
              ("" if name in models else "  <- not in your list; set LLM_MODEL / EMBEDDING_MODEL"))

step("embeddings", lambda: f"dim={GeminiEmbedder(s.gemini_api_key, emb_model).embed_documents(['hello', 'world']).shape[1]}")
step("JSON generation", lambda: str(GeminiLLM(s.gemini_api_key, llm_model).generate_json(
    "Reply with a JSON object.", 'Return {"ok": true}')))
