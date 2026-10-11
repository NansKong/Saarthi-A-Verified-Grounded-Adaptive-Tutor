"""Tests never read the real environment or .env, so a developer's API keys can't leak into CI
or trigger network calls."""
from pathlib import Path

import pytest

from src.retrieval.bm25 import BM25
from src.retrieval.config import Settings
from src.retrieval.embeddings import HashingEmbedder
from src.retrieval.rerank import LexicalReranker
from src.retrieval.retriever import HybridRetriever
from src.graph.graph import KnowledgeGraph
from src.retrieval.store import DEFAULT_GRAPH, CorpusStore


def make_settings(**kw) -> Settings:
    base = dict(embedding_provider="auto", embedding_model="", rerank_provider="auto", rerank_model="",
                openai_api_key="", gemini_api_key="", cache_dir=Path(".pod_b_test_cache"), candidate_pool=20)
    base.update(kw)
    return Settings(**base)


@pytest.fixture(scope="session")
def store():
    return CorpusStore.from_json()


@pytest.fixture(scope="session")
def retriever(store):
    idf = BM25([u.searchable_text() for u in store.all()])._idf
    return HybridRetriever(store, HashingEmbedder(), LexicalReranker(idf), 20,
                           info={"embedding_choice": "test", "rerank_choice": "test"})


@pytest.fixture
def graph():
    """Fresh copy per test (graph functions mutate)."""
    return KnowledgeGraph.load(DEFAULT_GRAPH)
