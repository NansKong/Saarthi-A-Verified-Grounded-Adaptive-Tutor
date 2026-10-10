"""Pod B HTTP surface (mounted under /pod-b). Every handler reads `rt.bundle` once, so a concurrent ingest or
graph rebuild can swap the knowledge base without a request ever seeing a half-built one."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .answer import GroundedAnswerer
from .config import Settings
from .graph import KnowledgeGraph, tag_units
from .retriever import HybridRetriever
from .runtime import MAX_UNITS_PER_INGEST, Runtime, build_bundle, load_startup, prune_graph
from .schemas import (AnswerResponse, Citation, ConceptNode, ContentUnit, SourceType, Topic, make_citation)
from .security import RateLimiter, make_admin_guard
from .store import CorpusStore

log = logging.getLogger("pod_b")
_EXCLUDE = {"embedding"}  # vectors are large and useless to the UI
_EXCLUDE_EACH = {"__all__": _EXCLUDE}


class SearchHitOut(BaseModel):
    unit_id: str
    text: str
    image_caption: Optional[str] = None
    citation: Citation
    relevance: float  # reranker score 0..1 (backend-specific; used by the refusal gate)
    bm25: float
    dense: float


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    source_types: Optional[list[SourceType]] = None
    source_ids: Optional[list[str]] = None
    allow_outside_knowledge: bool = False  # if True, a refused question may carry a clearly-labelled outside note
    student_context: Optional[str] = Field(None, max_length=1000)  # hook for Pod C's learner model


class IngestRequest(BaseModel):
    units: list[ContentUnit] = Field(..., min_length=1, max_length=MAX_UNITS_PER_INGEST)
    replace_sources: bool = True  # re-ingesting a source_id replaces its previous units


def build_router(rt: Runtime, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/pod-b", tags=["pod-b"])
    limiter = RateLimiter(settings.rate_limit_per_min)
    admin = Depends(make_admin_guard(settings.admin_token))

    def rate_limit(request: Request) -> None:
        limiter.check(request.client.host if request.client else "unknown")

    @router.get("/health")
    def health():
        b = rt.bundle
        return {"status": "ok", "units": len(b.store), "sources": b.store.sources(), "version": b.version,
                "mode": b.answerer.info()["mode"], "admin_protected": bool(settings.admin_token)}

    @router.get("/units", response_model=list[ContentUnit], response_model_exclude=_EXCLUDE_EACH)
    def list_units(source_id: Optional[str] = None, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
        store = rt.bundle.store
        units = store.by_source(source_id) if source_id else store.all()
        return units[offset: offset + limit]

    @router.get("/units/{unit_id}", response_model=ContentUnit, response_model_exclude=_EXCLUDE)
    def get_unit(unit_id: str):
        unit = rt.bundle.store.get(unit_id)
        if unit is None:
            raise HTTPException(status_code=404, detail=f"unit {unit_id!r} not found")
        return unit

    # ---------------- retrieval ----------------
    @router.get("/retrieval/info")
    def retrieval_info():
        """Which embedder/reranker is active and why - check this after adding an API key."""
        return rt.bundle.retriever.info()

    @router.get("/search", response_model=list[SearchHitOut])
    def search(q: str = Query(..., min_length=1, max_length=2000), k: int = Query(5, ge=1, le=20),
               source_type: Optional[list[SourceType]] = Query(None), source_id: Optional[list[str]] = Query(None)):
        hits = rt.bundle.retriever.search(q, k, source_types=source_type, source_ids=source_id)
        return [SearchHitOut(unit_id=h.unit.unit_id, text=h.unit.text, image_caption=h.unit.image_caption,
                             citation=make_citation(h.unit), relevance=h.relevance, bm25=h.bm25, dense=h.dense)
                for h in hits]

    # ---------------- grounded tutor ----------------
    @router.post("/ask", response_model=AnswerResponse, dependencies=[Depends(rate_limit)])
    def ask(req: AskRequest):
        """Source-grounded answer. status: grounded | partial | refused. Every supported claim carries citations
        with deep links; unsupported or outside-material content is listed separately."""
        t0 = time.monotonic()
        resp = rt.bundle.answerer.answer(
            req.question, history=[t.model_dump() for t in req.history], source_types=req.source_types,
            source_ids=req.source_ids, allow_outside_knowledge=req.allow_outside_knowledge,
            student_context=req.student_context)
        log.info("ask status=%s mode=%s sources=%d q_len=%d ms=%d", resp.status.value, resp.mode, len(resp.sources),
                 len(req.question), (time.monotonic() - t0) * 1000)
        return resp

    @router.get("/ask/info")
    def ask_info():
        return rt.bundle.answerer.info()

    # ---------------- knowledge graph ----------------
    def _concept_or_404(graph: KnowledgeGraph, cid: str) -> ConceptNode:
        c = graph.concepts.get(cid)
        if c is None:
            raise HTTPException(status_code=404, detail=f"concept {cid!r} not found")
        return c

    @router.get("/graph")
    def get_graph():
        """Flow-map data: nodes, prerequisite->dependent edges (with validation signals), topic tree."""
        return rt.bundle.graph.viz()

    @router.get("/topics", response_model=list[Topic])
    def list_topics():
        return list(rt.bundle.graph.topics.values())

    @router.get("/concepts", response_model=list[ConceptNode])
    def list_concepts(topic_id: Optional[str] = None, q: Optional[str] = None):
        g = rt.bundle.graph
        if q:
            return [c for c, _ in g.match_concepts(q, k=10)]
        return g.concepts_in_topic(topic_id) if topic_id else list(g.concepts.values())

    @router.get("/concepts/{concept_id}")
    def get_concept(concept_id: str):
        g = rt.bundle.graph
        c = _concept_or_404(g, concept_id)
        return {
            "concept": c,
            "topic_chain": [g.topics[t].name for t in reversed(g.topic_chain(c.topic))],
            "prerequisites": [{"concept_id": p, "name": g.concepts[p].name} for p in c.prerequisites],
            "all_prerequisites": g.prerequisites_of(concept_id, transitive=True),
            "dependents": [{"concept_id": d, "name": g.concepts[d].name} for d in g.dependents_of(concept_id)],
        }

    @router.get("/concepts/{concept_id}/units")
    def concept_units(concept_id: str, include_related: bool = False):
        """Source units for a concept - what Pod C writes questions from. Evidence units first;
        include_related adds any other unit tagged with the concept."""
        b = rt.bundle
        c = _concept_or_404(b.graph, concept_id)
        ids = list(c.evidence_units)
        if include_related:
            ids += [u.unit_id for u in b.store.all() if concept_id in u.concept_ids and u.unit_id not in ids]
        return [{"unit_id": u.unit_id, "text": u.text, "image_caption": u.image_caption,
                 "evidence": u.unit_id in c.evidence_units, "citation": make_citation(u)}
                for u in (b.store.get(i) for i in ids) if u]

    @router.get("/coverage")
    def coverage():
        b = rt.bundle
        units = b.store.all()
        return {
            "units": len(units),
            "units_with_concepts": sum(1 for u in units if u.concept_ids),
            "untagged_units": [u.unit_id for u in units if not u.concept_ids],
            "concepts": len(b.graph.concepts),
            "concepts_without_evidence": [c.concept_id for c in b.graph.concepts.values() if not c.evidence_units],
            "edges_validated": sum(len(c.prerequisites) for c in b.graph.concepts.values()),
            "edges_unvalidated": sum(1 for c in b.graph.concepts.values() for e in c.prerequisite_edges if not e.validated),
            "integrity_problems": b.graph.integrity_problems(b.store),
        }

    # ---------------- live ingestion (state-changing: admin-guarded) ----------------
    @router.post("/ingest/units", dependencies=[admin])
    def ingest_units(req: IngestRequest):
        """Add or replace units from Pod A without restarting. Indexed and tagged immediately; run
        POST /graph/rebuild afterwards if `graph_stale` is true so new concepts appear."""
        try:
            return rt.ingest(req.units, req.replace_sources)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    @router.post("/graph/rebuild", status_code=202, dependencies=[admin])
    def graph_rebuild():
        """Rebuild the concept graph with the LLM in the background (costs API calls). Poll /graph/status."""
        try:
            return rt.start_graph_rebuild()
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=503, detail=str(e))

    @router.get("/graph/status")
    def graph_status():
        return rt.rebuild_status()

    return router


def sources_router(directory: Path) -> APIRouter:
    """Serve original uploads so citation links open. Lookup is by listing the directory and comparing names,
    never by joining user input into a path, so traversal is impossible. Page/slide/time anchors in the URL
    fragment are for the frontend viewer to act on."""
    router = APIRouter(tags=["sources"])

    @router.get("/sources/{source_id}")
    def get_source(source_id: str):
        for p in sorted(Path(directory).iterdir()):
            if p.is_file() and source_id in (p.stem, p.name):
                return FileResponse(p)
        raise HTTPException(status_code=404, detail="source not found")

    return router


def create_app(store: Optional[CorpusStore] = None, retriever: Optional[HybridRetriever] = None,
               graph: Optional[KnowledgeGraph] = None, answerer: Optional[GroundedAnswerer] = None,
               settings: Optional[Settings] = None, persist: Optional[bool] = None) -> FastAPI:
    settings = settings or Settings.from_env()
    injected = any(x is not None for x in (store, retriever, graph, answerer))
    if store is None or graph is None:
        s0, g0 = load_startup(settings)
        store, graph = store or s0, graph or g0
    prune_graph(graph, store)
    tag_units(graph, store)  # back-fill unit.topic_ids / concept_ids (Pod B owns these fields)
    rt = Runtime(build_bundle(settings, store, graph, retriever, answerer), settings,
                 persist=(not injected) if persist is None else persist)

    app = FastAPI(title="Saarthi - Pod B (graph, retrieval, grounding)")
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                           allow_headers=["*"], allow_credentials=False)
    app.include_router(build_router(rt, settings))
    if settings.sources_dir and Path(settings.sources_dir).is_dir():
        app.include_router(sources_router(Path(settings.sources_dir)))
    if not settings.admin_token:
        log.warning("POD_B_ADMIN_TOKEN is not set: /ingest and /graph/rebuild are open. Fine locally; set it before sharing.")
    app.state.runtime = rt
    return app


app = create_app()  # `uvicorn pod_b.api:app --reload`
