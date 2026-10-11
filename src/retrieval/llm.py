"""LLM access behind one tiny interface. Today: Gemini (REST, no SDK). Add another provider by
implementing `generate_json` and extending `make_llm`; nothing else in Pod B changes."""
from __future__ import annotations

import json
import os
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


class ReplicateLLM:
    DEFAULT_MODEL = "openai/gpt-4o-mini"

    def __init__(self, api_key: str, model: str = ""):
        self.model = model or os.getenv("REPLICATE_MODEL") or self.DEFAULT_MODEL
        self.name = f"replicate:{self.model}"
        self._key = api_key
        os.environ["REPLICATE_API_TOKEN"] = api_key
        os.environ["REPLICATE_API_KEY"] = api_key
        self.calls = 0

    def generate_json(self, system: str, prompt: str) -> dict:
        import replicate
        self.calls += 1
        combined = f"System Instruction: {system}\n\nTask: {prompt}\n\nCRITICAL: Respond ONLY with a valid JSON object."
        last: Exception = LLMError("unreachable")
        for attempt in range(2):
            try:
                output = replicate.run(
                    self.model,
                    input={
                        "prompt": combined if attempt == 0 else combined + "\n\nStrict JSON only.",
                        "temperature": 0.1,
                    },
                )
                raw = "".join(output) if isinstance(output, (list, tuple)) or hasattr(output, "__iter__") else str(output)
                return parse_json_loose(raw)
            except Exception as e:
                last = e
        raise LLMError(f"Replicate {self.model} error: {last}")


class GroqLLM:
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str, model: str = ""):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model or os.getenv("GROQ_MODEL") or self.DEFAULT_MODEL
        self.name = f"groq:{self.model}"
        self.calls = 0

    def generate_json(self, system: str, prompt: str) -> dict:
        self.calls += 1
        last: Exception = LLMError("unreachable")
        for attempt in range(2):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                text = resp.choices[0].message.content or "{}"
                return parse_json_loose(text)
            except Exception as e:
                last = e
        raise LLMError(f"Groq {self.model} error: {last}")


def make_llm(s: Settings, client: Optional[httpx.Client] = None) -> tuple[Optional[LLM], str]:
    """Returns (llm or None, reason). None means 'no LLM configured' and callers must degrade."""
    p = s.llm_provider
    rep_key = s.replicate_api_key
    groq_key = s.groq_api_key

    if p == "none":
        return None, "LLM_PROVIDER=none"
    if p == "replicate":
        if not rep_key:
            raise ConfigError("LLM_PROVIDER=replicate but REPLICATE_API_KEY is not set")
        return ReplicateLLM(rep_key, os.getenv("REPLICATE_MODEL", "")), f"replicate -> {os.getenv('REPLICATE_MODEL', 'openai/gpt-4o-mini')}"
    if p == "groq":
        if not groq_key:
            raise ConfigError("LLM_PROVIDER=groq but GROQ_API_KEY is not set")
        return GroqLLM(groq_key, os.getenv("GROQ_MODEL", "")), f"groq -> {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}"
    if p == "gemini":
        if not s.gemini_api_key:
            raise ConfigError("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set")
        return GeminiLLM(s.gemini_api_key, s.llm_model, client=client), "gemini"

    if p == "auto":
        # Check providers in priority: Replicate (gpt-4o-mini) -> Groq (llama-3.3) -> Gemini -> none
        if rep_key:
            model = os.getenv("REPLICATE_MODEL", "openai/gpt-4o-mini")
            return ReplicateLLM(rep_key, model), f"auto -> replicate ({model})"
        if groq_key:
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            return GroqLLM(groq_key, model), f"auto -> groq ({model})"
        if s.gemini_api_key:
            return GeminiLLM(s.gemini_api_key, s.llm_model, client=client), "auto -> gemini"
        return None, "auto -> none (no API keys configured)"

    raise ConfigError(f"unknown LLM_PROVIDER={p!r} (use auto|replicate|groq|gemini|none)")
