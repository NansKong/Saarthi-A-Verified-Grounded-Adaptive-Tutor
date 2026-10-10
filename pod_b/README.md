# Saarthi - Pod B (concept graph, retrieval, grounding)

## Run
    pip install -r requirements.txt
    python -m pytest -q
    uvicorn pod_b.api:app --reload      # then open http://127.0.0.1:8000/docs

Point at Pod A's real units with `POD_B_CORPUS=/path/to/units.json` (same shape as `pod_b/mock/mock_corpus.json`).

## Using your Gemini key
    cp .env.example .env   # then add the line:  GEMINI_API_KEY=your-key   (.env is git-ignored; never commit it)
    pip install -r requirements.txt
    python scripts/check_gemini.py     # verifies key, lists usable models, tests embeddings + JSON generation
    python scripts/build_graph.py      # builds the concept graph with Gemini; scores it vs the hand-labelled demo graph
    uvicorn pod_b.api:app --reload     # serves the graph; /pod-b/graph, /concepts, /coverage, /search

## Grounded tutor (step 4)
    python scripts/calibrate.py        # measure refusal thresholds for your backend (re-run after changing models)
    python scripts/eval_grounding.py   # retrieval/citation/refusal smoke metrics (extractive; + generative if a key is set)
`POST /pod-b/ask {"question": "...", "history": [...]}` returns `status` (grounded | partial | refused), numbered
`sources` with deep links, `claims`, `outside_knowledge`, and `retrieved` unit ids (for RAGAS-style evaluation by Pod D).
`GET /pod-b/ask/info` shows the active mode and whether thresholds are calibrated.
`eval_results/grounding_dev_eval.json` was produced with the built-in fallback backend and NO LLM, on a 34-query set
written by the same author as the corpus - optimistic, and only a regression baseline.

## Live ingest, demo, docs (step 5)
    python scripts/demo.py --pause     # scripted tour for the demo video (no server needed)
    uvicorn pod_b.api:app --reload     # then POST /pod-b/ingest/units to add Pod A's units without restarting
Set `POD_B_ADMIN_TOKEN` before sharing the server (guards ingest and graph rebuild), `POD_B_CORS_ORIGINS` for the
frontend's origin, `POD_B_SOURCES_DIR` to serve original files at `/sources/{source_id}`.
Ingested units persist in `.pod_b_cache/`; delete that folder to return to the bundled demo corpus.
Architecture, grounding method, evaluation and limitations: `docs/ARCHITECTURE.md`.

## Adding API keys / better models later (no code changes)
    cp .env.example .env        # then uncomment a key, e.g. OPENAI_API_KEY=... or GEMINI_API_KEY=...
    pip install sentence-transformers   # free local embeddings + cross-encoder reranker
    python scripts/retrieval_check.py   # shows which backend is active and its quality numbers
`GET /pod-b/retrieval/info` reports the active embedder/reranker. Embeddings are cached in `.pod_b_cache/`,
so a paid API embeds each unit once. If you change embedding model, retrieval re-embeds automatically.

## Layout
- `pod_b/schemas.py` - shared contracts (ContentUnit, ConceptNode, Topic, Citation/AnswerResponse)
- `pod_b/store.py`   - loads and validates units
- `pod_b/config.py`  - env/.env settings (provider choice, keys)
- `pod_b/embeddings.py`, `rerank.py`, `bm25.py`, `retriever.py` - hybrid retrieval (BM25 + dense -> RRF -> rerank)
- `pod_b/llm.py`, `graph.py`, `graph_builder.py` - Gemini adapter; graph model + validation; LLM build pipeline
- `pod_b/answer.py`, `calibration.py` - grounded answering; per-backend refusal thresholds
- `pod_b/runtime.py`, `security.py` - live ingest/rebuild with atomic swap; rate limit and admin guard
- `pod_b/golden.py`  - hand-labelled retrieval queries; `scripts/retrieval_check.py` scores them
- `pod_b/api.py`     - FastAPI router under `/pod-b`
- `pod_b/mock/`      - 28-unit demo corpus (slides, textbook pages, lecture video)

## Build steps
1. [done] Skeleton, schemas, mock corpus, read API
2. [done] Hybrid retrieval (BM25 + embeddings + reranker), pluggable providers, `/search`
3. [done] Concept graph (LLM extraction, evidence-validated prerequisites, DAG, unit tagging, graph API)
4. [done] Grounded answerer: `POST /pod-b/ask` (claim-level citations, two-stage refusal, extractive fallback, follow-ups)
5. [done] Live ingest, graph rebuild job, admin token, rate limit, CORS, source serving, demo script, docs/ARCHITECTURE.md
