"""LLM access behind one tiny interface. Today: Gemini (REST, no SDK). Add another provider by
implementing `generate_json` and extending `make_llm`; nothing else in Pod B changes."""
from __future__ import annotations

import json
import re
import time
from typing import Callable, Optional, Protocol

import httpx

from .config import Settings
from .embeddings import ConfigError, _post_json


class LLMError(RuntimeError):
    pass


class LLM(Protocol):
    name: str

    def generate_json(self, system: str, prompt: str) -> dict: ...


def parse_json_loose(text: str) -> dict:
    """Parse a JSON object even if the model wrapped it in ``` fences or added chatter."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        a, b = t.find("{"), t.rfind("}")
        if a != -1 and b > a:
            return json.loads(t[a : b + 1])
        raise


class GeminiLLM:
    DEFAULT_MODEL = "gemini-2.5-flash"  # override with LLM_MODEL; scripts/check_gemini.py lists what your key can use
    BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str = "", client: Optional[httpx.Client] = None,
                 sleep: Callable[[float], None] = time.sleep, temperature: float = 0.1):
        self.model = model or self.DEFAULT_MODEL
        self.name = f"gemini:{self.model}"
        self._key, self._sleep, self._temp = api_key, sleep, temperature
        self._client = client or httpx.Client()
        self.calls = 0

    def _generate(self, system: str, prompt: str) -> str:
        self.calls += 1
        data = _post_json(
            self._client, f"{self.BASE}/models/{self.model}:generateContent",
            {"x-goog-api-key": self._key},
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": self._temp, "responseMimeType": "application/json"},
            },
            sleep=self._sleep, timeout=180, retries=6,
        )
        cands = data.get("candidates") or []
        if not cands:
            raise LLMError(f"Gemini returned no candidates (blocked?): {str(data.get('promptFeedback'))[:200]}")
        parts = cands[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text.strip():
            raise LLMError(f"Gemini returned empty text (finishReason={cands[0].get('finishReason')})")
        return text

    def generate_json(self, system: str, prompt: str) -> dict:
        last: Exception = LLMError("unreachable")
        for attempt in range(2):  # one retry if the model emits malformed JSON
            text = self._generate(system, prompt if attempt == 0 else prompt + "\n\nReturn ONLY valid JSON.")
            try:
                return parse_json_loose(text)
            except json.JSONDecodeError as e:
                last = e
        raise LLMError(f"model did not return valid JSON: {last}")


def make_llm(s: Settings, client: Optional[httpx.Client] = None) -> tuple[Optional[LLM], str]:
    """Returns (llm or None, reason). None means 'no LLM configured' and callers must degrade."""
    p = s.llm_provider
    if p == "none":
        return None, "LLM_PROVIDER=none"
    if p == "auto":
        p = "gemini" if s.gemini_api_key else "none"
        if p == "none":
            return None, "auto -> none (no GEMINI_API_KEY)"
        reason = "auto -> gemini"
    else:
        reason = f"LLM_PROVIDER={p}"
    if p == "gemini":
        if not s.gemini_api_key:
            raise ConfigError("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set")
        return GeminiLLM(s.gemini_api_key, s.llm_model, client=client), reason
    raise ConfigError(f"unknown LLM_PROVIDER={p!r} (use auto|gemini|none)")
