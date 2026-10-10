"""Hybrid retrieval: BM25 + dense embeddings -> reciprocal-rank fusion -> rerank.

Design notes
* Pod B embeds both units and queries with ITS OWN embedder. Pod A's `unit.embedding` is ignored,
  because query and document vectors must come from the same model.
* RRF scores are rank-based, so they say nothing about absolute relevance. `relevance` (from the
  reranker, 0..1) is the signal the refusal gate will use in step 4. It is backend-specific, so the
  gate threshold has to be calibrated per backend, not hard-coded.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import httpx
import numpy as np

from .bm25 import BM25
from .config import Settings
from .embeddings import CachedEmbedder, Embedder, EmbeddingCache, HashingEmbedder, make_embedder
from .rerank import LexicalReranker, Reranker, make_reranker
from .graph import KnowledgeGraph
from .schemas import ContentUnit, SourceType
from .store import CorpusStore

RRF_K = 60
CONCEPT_BOOST = 0.2  # added to the ordering score of a matched concept's evidence units


@dataclass
class SearchHit:
    unit: ContentUnit
    score: float  # ordering score = relevance + concept boost
    relevance: float  # reranker score in [0, 1]; NOT boosted - this is what the refusal gate reads
    rrf: float  # fused first-stage score
    bm25: float
    dense: float  # cosine similarity


class HybridRetriever:
    def __init__(self, store: CorpusStore, embedder: Embedder, reranker: Reranker,
                 candidate_pool: int = 20, info: Optional[dict] = None,
                 graph: Optional[KnowledgeGraph] = None):
        self.store, self.embedder, self.reranker, self.graph = store, embedder, reranker, graph
        self.pool = candidate_pool
        self._info = info or {}
        self.units = store.all()
        texts = [u.searchable_text() for u in self.units]
        self._bm25 = BM25(texts)
        self._emb = embedder.embed_documents(texts)  # (n_units, dim), L2-normalised
        self._texts = texts

    # ------------------------------------------------------------------ #
    def with_store(self, store: CorpusStore, graph: Optional[KnowledgeGraph]) -> "HybridRetriever":
        """New retriever over a new corpus, reusing the embedder (its disk cache means only unseen units are
        embedded). The lexical reranker's IDF is corpus-specific, so it is refit."""
        rr = self.reranker
        if isinstance(rr, LexicalReranker):
            rr = LexicalReranker(BM25([u.searchable_text() for u in store.all()])._idf)
        return HybridRetriever(store, self.embedder, rr, self.pool, info=self._info, graph=graph)

    def backend_key(self) -> str:
        """Identifies the relevance scale; refusal thresholds are calibrated per key."""
        return f"{self.embedder.name}|{self.reranker.name}"

    def concept_boost(self, query: str) -> dict[str, float]:
        """If the query names a known concept, its evidence units (the chunks that DEFINE it) get a boost.
        Fixes 'what is the chain rule' ranking a passing mention above the definition."""
        if self.graph is None:
            return {}
        out: dict[str, float] = {}
        for concept, sc in self.graph.match_concepts(query, k=3):
            if sc >= 1.0:  # the concept's name/alias appears in the question as a phrase
                for uid in concept.evidence_units:
                    out[uid] = CONCEPT_BOOST
        return out

    def info(self) -> dict:
        return {**self._info, "embedder": self.embedder.name, "reranker": self.reranker.name,
                "units": len(self.units), "dim": int(self._emb.shape[1]) if self._emb.size else 0}

    def search(self, query: str, k: int = 5, *,
               source_types: Optional[Iterable[SourceType]] = None,
               source_ids: Optional[Iterable[str]] = None) -> list[SearchHit]:
        if not query.strip() or not self.units:
            return []
        types = set(source_types) if source_types else None
        sids = set(source_ids) if source_ids else None
        allowed = [i for i, u in enumerate(self.units)
                   if (types is None or u.source_type in types) and (sids is None or u.source_id in sids)]
        if not allowed:
            return []

        bm = np.array(self._bm25.scores(query))
        dense = self._emb @ self.embedder.embed_query(query)

        # rank within the allowed subset; BM25 only ranks docs that matched at least one term
        sparse_rank = {i: r for r, i in enumerate(sorted((i for i in allowed if bm[i] > 0), key=lambda i: -bm[i]))}
        dense_rank = {i: r for r, i in enumerate(sorted(allowed, key=lambda i: -dense[i]))}
        rrf = {i: (1 / (RRF_K + sparse_rank[i] + 1) if i in sparse_rank else 0.0)
                  + 1 / (RRF_K + dense_rank[i] + 1) for i in allowed}

        boost = self.concept_boost(query)
        pool = sorted(allowed, key=lambda i: -rrf[i])[: max(self.pool, k)]
        allowed_set, in_pool = set(allowed), set(pool)
        pool += [i for i, u in enumerate(self.units)  # make sure definition chunks are always considered
                 if u.unit_id in boost and i in allowed_set and i not in in_pool]
        rel = self.reranker.score(query, [self._texts[i] for i in pool])
        scored = [(i, r, r + boost.get(self.units[i].unit_id, 0.0)) for i, r in zip(pool, rel)]
        scored.sort(key=lambda t: (-t[2], -rrf[t[0]]))
        return [SearchHit(unit=self.units[i], score=sc, relevance=r, rrf=rrf[i],
                          bm25=float(bm[i]), dense=float(dense[i])) for i, r, sc in scored[:k]]


def build_retriever(store: CorpusStore, settings: Optional[Settings] = None,
                    client: Optional[httpx.Client] = None, graph: Optional[KnowledgeGraph] = None) -> HybridRetriever:
    s = settings or Settings.from_env()
    embedder, e_reason = make_embedder(s, client)
    if not isinstance(embedder, HashingEmbedder):  # hashing is free and instant; cache the rest
        embedder = CachedEmbedder(embedder, EmbeddingCache(Path(s.cache_dir) / "embeddings.sqlite"))
    idf = BM25([u.searchable_text() for u in store.all()])._idf  # shared IDF for the lexical reranker
    reranker, r_reason = make_reranker(s, idf)
    return HybridRetriever(store, embedder, reranker, s.candidate_pool,
                           info={"embedding_choice": e_reason, "rerank_choice": r_reason}, graph=graph)
