"""Measure retrieval quality for whatever backend is currently configured.
Run before and after adding an API key (or installing sentence-transformers) to see the difference:

    python scripts/retrieval_check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pod_b.golden import LEXICAL, OFF_MATERIAL, SEMANTIC, evaluate  # noqa: E402
from pod_b.retriever import build_retriever  # noqa: E402
from pod_b.store import CorpusStore  # noqa: E402

r = build_retriever(CorpusStore.from_json())
info = r.info()
print(f"embedder : {info['embedder']}   ({info['embedding_choice']})")
print(f"reranker : {info['reranker']}   ({info['rerank_choice']})")
print(f"units    : {info['units']}\n")
for name, items in (("lexical queries ", LEXICAL), ("semantic queries", SEMANTIC)):
    h1, _ = evaluate(r, items, 1)
    h3, mrr = evaluate(r, items, 3)
    print(f"{name}  hit@1={h1:.2f}  hit@3={h3:.2f}  MRR={mrr:.2f}  (n={len(items)})")

in_scope = sorted(r.search(q, 1)[0].relevance for q, _ in LEXICAL + SEMANTIC)
off = [(q, (r.search(q, 1) or [None])[0]) for q in OFF_MATERIAL]
print(f"\ntop-hit relevance, in-scope : min={in_scope[0]:.2f}  median={in_scope[len(in_scope)//2]:.2f}")
for q, h in off:
    print(f"top-hit relevance, off-topic: {h.relevance if h else 0.0:.2f}   <- {q!r}")
print("\nNote: relevance scales differ per backend; step 4 calibrates the refusal threshold per backend.")
