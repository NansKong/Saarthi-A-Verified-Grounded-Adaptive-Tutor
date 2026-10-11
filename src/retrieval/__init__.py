"""
src/retrieval - Pod B: Hybrid Search, Grounded Tutor & Confidence-Gated Citations
Exports:
- HybridRetriever: BM25 + Dense vector retrieval with reciprocal rank fusion
- GroundedAnswerer: Claim-level citation generator with confidence-gated refusal
- BM25Index / BM25: Lexical inverted index
- CrossEncoderReranker: Neural reranker
- CorpusStore: In-memory/persisted ContentUnit store
- AnswerResponse, Citation, Claim: Citation chip and refusal schemas
"""

from src.retrieval.retriever import HybridRetriever, SearchHit
from src.retrieval.answer import GroundedAnswerer
from src.retrieval.bm25 import BM25
from src.retrieval.rerank import CrossEncoderReranker
from src.retrieval.embeddings import make_embedder
from src.retrieval.store import CorpusStore
from src.retrieval.schemas import (
    AnswerResponse,
    AnswerStatus,
    Citation,
    Claim,
    Location,
    make_citation,
)

__all__ = [
    "HybridRetriever",
    "SearchHit",
    "GroundedAnswerer",
    "BM25",
    "CrossEncoderReranker",
    "make_embedder",
    "CorpusStore",
    "AnswerResponse",
    "AnswerStatus",
    "Citation",
    "Claim",
    "Location",
    "make_citation",
]
