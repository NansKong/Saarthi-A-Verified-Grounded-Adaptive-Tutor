"""Embedding backends behind one interface.

    HashingEmbedder   built-in, zero dependencies, lexical only (CI / no-keys fallback)
    LocalEmbedder     sentence-transformers, free, runs on your machine (default when installed)
    OpenAIEmbedder    hosted, needs OPENAI_API_KEY
    GeminiEmbedder    hosted, needs GEMINI_API_KEY

Switching backend never needs code changes: set env vars (see config.py / .env.example).
Document embeddings are cached on disk, so paid APIs are only called once per unit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
import time
import zlib
from pathlib import Path
from typing import Callable, Optional, Protocol

import httpx
import numpy as np

from .config import Settings
from .text import tokenize


class ConfigError(RuntimeError):
    """Raised when a provider is requested explicitly but cannot be used."""


class Embedder(Protocol):
    name: str  # unique per provider+model; used for cache keys

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...


def _normalize(m: np.ndarray) -> np.ndarray:
    m = np.asarray(m, dtype=np.float32)
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1.0, norms)


# --------------------------------------------------------------------------- #
class HashingEmbedder:
    """Feature-hashed bag of stemmed unigrams+bigrams. Deterministic. No semantics."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.name = f"hash:{dim}"

    def _vec(self, text: str) -> np.ndarray:
        toks = tokenize(text)
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        v = np.zeros(self.dim, dtype=np.float32)
        counts: dict[str, int] = {}
        for f in feats:
            counts[f] = counts.get(f, 0) + 1
        for f, c in counts.items():
            h = zlib.crc32(f.encode())
            sign = 1.0 if (h >> 31) & 1 else -1.0
            v[h % self.dim] += sign * (1.0 + np.log(c))
        return v

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return _normalize(np.stack([self._vec(t) for t in texts])) if texts else np.zeros((0, self.dim), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return _normalize(self._vec(text)[None, :])[0]


# --------------------------------------------------------------------------- #
class LocalEmbedder:
    """sentence-transformers. First use downloads the model (~130 MB for the default)."""

    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
    _QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # bge convention

    def __init__(self, model: str = ""):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.model_name = model or self.DEFAULT_MODEL
        self.name = f"local:{self.model_name}"
        self._model = SentenceTransformer(self.model_name)
        self._prefix = self._QUERY_PREFIX if "bge" in self.model_name.lower() else ""

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return _normalize(self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False))

    def embed_query(self, text: str) -> np.ndarray:
        return _normalize(self._model.encode([self._prefix + text], normalize_embeddings=True)[0])


# --------------------------------------------------------------------------- #
def _post_json(client: httpx.Client, url: str, headers: dict, payload: dict,
               *, retries: int = 4, sleep: Callable[[float], None] = time.sleep, timeout: float = 60) -> dict:
    """POST with exponential backoff on 429/5xx. Errors never include the API key."""
    for attempt in range(retries):
        resp = client.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < retries - 1:
                try:
                    wait = float(resp.headers.get("retry-after", 0))
                except ValueError:
                    wait = 0.0
                sleep(min(60.0, max(2 ** attempt, wait)))
                continue
        if resp.status_code >= 400:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text[:300]}")
        return resp.json()
    raise RuntimeError("API: retries exhausted")


class OpenAIEmbedder:
    DEFAULT_MODEL = "text-embedding-3-small"
    BATCH = 96

    def __init__(self, api_key: str, model: str = "", base_url: str = "https://api.openai.com/v1",
                 client: Optional[httpx.Client] = None, sleep: Callable[[float], None] = time.sleep):
        self.model = model or self.DEFAULT_MODEL
        self.name = f"openai:{self.model}"
        self._key, self._base, self._sleep = api_key, base_url.rstrip("/"), sleep
        self._client = client or httpx.Client()

    def _embed(self, texts: list[str]) -> np.ndarray:
        out: list[list[float]] = []
        for i in range(0, len(texts), self.BATCH):
            data = _post_json(
                self._client, f"{self._base}/embeddings",
                {"Authorization": f"Bearer {self._key}"},
                {"model": self.model, "input": texts[i : i + self.BATCH]},
                sleep=self._sleep,
            )
            out += [d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"])]
        return _normalize(np.array(out))

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._embed(texts) if texts else np.zeros((0, 1), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text])[0]


class GeminiEmbedder:
    DEFAULT_MODEL = "gemini-embedding-001"
    BATCH = 100
    BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str = "", client: Optional[httpx.Client] = None,
                 sleep: Callable[[float], None] = time.sleep):
        self.model = model or self.DEFAULT_MODEL
        self.name = f"gemini:{self.model}"
        self._key, self._sleep = api_key, sleep
        self._client = client or httpx.Client()

    def _embed(self, texts: list[str], task: str) -> np.ndarray:
        out: list[list[float]] = []
        for i in range(0, len(texts), self.BATCH):
            reqs = [
                {"model": f"models/{self.model}", "taskType": task,
                 "content": {"parts": [{"text": t}]}}
                for t in texts[i : i + self.BATCH]
            ]
            data = _post_json(
                self._client, f"{self.BASE}/models/{self.model}:batchEmbedContents",
                {"x-goog-api-key": self._key}, {"requests": reqs}, sleep=self._sleep,
            )
            out += [e["values"] for e in data["embeddings"]]
        return _normalize(np.array(out))

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._embed(texts, "RETRIEVAL_DOCUMENT") if texts else np.zeros((0, 1), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text], "RETRIEVAL_QUERY")[0]


# --------------------------------------------------------------------------- #
class EmbeddingCache:
    """sqlite cache: (embedder name + text hash) -> vector. Survives restarts."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path))
        self._db.execute("CREATE TABLE IF NOT EXISTS emb (k TEXT PRIMARY KEY, v BLOB NOT NULL)")

    @staticmethod
    def key(embedder_name: str, text: str) -> str:
        return hashlib.sha256(f"{embedder_name}\x00{text}".encode()).hexdigest()

    def get(self, k: str) -> Optional[np.ndarray]:
        row = self._db.execute("SELECT v FROM emb WHERE k=?", (k,)).fetchone()
        return np.frombuffer(row[0], dtype=np.float32) if row else None

    def put(self, k: str, v: np.ndarray) -> None:
        self._db.execute("INSERT OR REPLACE INTO emb VALUES (?,?)", (k, np.asarray(v, np.float32).tobytes()))
        self._db.commit()


class CachedEmbedder:
    """Wraps any embedder; only texts never seen before reach the (possibly paid) backend."""

    def __init__(self, inner: Embedder, cache: EmbeddingCache):
        self.inner, self.cache, self.name = inner, cache, inner.name
        self.api_calls = 0  # number of texts actually sent to the backend (for visibility/tests)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        keys = [self.cache.key(self.name, t) for t in texts]
        vecs: list[Optional[np.ndarray]] = [self.cache.get(k) for k in keys]
        missing = [i for i, v in enumerate(vecs) if v is None]
        if missing:
            fresh = self.inner.embed_documents([texts[i] for i in missing])
            self.api_calls += len(missing)
            for i, v in zip(missing, fresh):
                self.cache.put(keys[i], v)
                vecs[i] = np.asarray(v, np.float32)
        return np.stack(vecs) if vecs else np.zeros((0, 1), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.inner.embed_query(text)


# --------------------------------------------------------------------------- #
def make_embedder(s: Settings, client: Optional[httpx.Client] = None) -> tuple[Embedder, str]:
    """Pick a backend. Returns (embedder, human-readable reason) so /retrieval/info can show why."""
    p = s.embedding_provider
    have_local = importlib.util.find_spec("sentence_transformers") is not None

    if p == "auto":
        if s.openai_api_key:
            p = "openai"
        elif s.gemini_api_key:
            p = "gemini"
        elif have_local:
            p = "local"
        else:
            p = "hash"
        reason = f"auto -> {p}"
    else:
        reason = f"EMBEDDING_PROVIDER={p}"

    if p == "openai":
        if not s.openai_api_key:
            raise ConfigError("EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is not set")
        return OpenAIEmbedder(s.openai_api_key, s.embedding_model, client=client), reason
    if p == "gemini":
        if not s.gemini_api_key:
            raise ConfigError("EMBEDDING_PROVIDER=gemini but GEMINI_API_KEY is not set")
        return GeminiEmbedder(s.gemini_api_key, s.embedding_model, client=client), reason
    if p == "local":
        if not have_local:
            raise ConfigError("EMBEDDING_PROVIDER=local but sentence-transformers is not installed "
                              "(pip install sentence-transformers)")
        return LocalEmbedder(s.embedding_model), reason
    if p == "hash":
        return HashingEmbedder(), reason
    raise ConfigError(f"unknown EMBEDDING_PROVIDER={p!r} (use auto|openai|gemini|local|hash)")
