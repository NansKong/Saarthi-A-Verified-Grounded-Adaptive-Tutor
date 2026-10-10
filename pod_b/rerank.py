"""Rerankers. All return a relevance score in [0, 1] per document (higher = better).

    CrossEncoderReranker  sentence-transformers cross-encoder (best, local, free)
    LexicalReranker       IDF-weighted query coverage + bigram overlap (built-in fallback)
"""
from __future__ import annotations

import importlib.util
import math
from typing import Optional, Protocol

from .config import Settings
from .embeddings import ConfigError
from .text import tokenize


class Reranker(Protocol):
    name: str

    def score(self, query: str, docs: list[str]) -> list[float]: ...


class LexicalReranker:
    name = "lexical"

    def __init__(self, idf: Optional[dict[str, float]] = None):
        self._idf = idf or {}

    def score(self, query: str, docs: list[str]) -> list[float]:
        """IDF-weighted share of query terms present, plus a small bigram bonus.

        Known limit: it cannot tell a definition from a passing mention (both cover the query
        terms). I tried adding tf/density features; they made top-1 accuracy worse on the golden
        set (0.86 -> 0.79), so they were dropped. The cross-encoder fixes this, and in step 3 the
        concept graph's evidence units will give definition chunks a direct boost."""
        q = tokenize(query)
        if not q:
            return [0.0] * len(docs)
        qset = set(q)
        qbi = set(zip(q, q[1:]))
        w = {t: self._idf.get(t, 1.0) for t in qset}
        total = sum(w.values()) or 1.0
        out = []
        for d in docs:
            dt = tokenize(d)
            dset = set(dt)
            cover = sum(w[t] for t in qset if t in dset) / total
            bigram = (len(qbi & set(zip(dt, dt[1:]))) / len(qbi)) if qbi else 0.0
            out.append(min(1.0, 0.8 * cover + 0.2 * bigram))
        return out


class CrossEncoderReranker:
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model: str = ""):
        from sentence_transformers import CrossEncoder  # lazy import

        self.model_name = model or self.DEFAULT_MODEL
        self.name = f"cross-encoder:{self.model_name}"
        self._model = CrossEncoder(self.model_name)

    def score(self, query: str, docs: list[str]) -> list[float]:
        if not docs:
            return []
        logits = self._model.predict([(query, d) for d in docs], show_progress_bar=False)
        return [1.0 / (1.0 + math.exp(-float(x))) for x in logits]  # sigmoid


def make_reranker(s: Settings, idf: Optional[dict[str, float]] = None) -> tuple[Reranker, str]:
    p = s.rerank_provider
    have_local = importlib.util.find_spec("sentence_transformers") is not None
    if p == "auto":
        p = "cross-encoder" if have_local else "lexical"
        reason = f"auto -> {p}"
    else:
        reason = f"RERANK_PROVIDER={p}"
    if p == "cross-encoder":
        if not have_local:
            raise ConfigError("RERANK_PROVIDER=cross-encoder but sentence-transformers is not installed")
        return CrossEncoderReranker(s.rerank_model), reason
    if p in ("lexical", "none"):
        return LexicalReranker(idf), reason
    raise ConfigError(f"unknown RERANK_PROVIDER={p!r} (use auto|cross-encoder|lexical|none)")
