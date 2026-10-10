import threading
import time

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from pod_b.answer import GroundedAnswerer
from pod_b.api import create_app
from pod_b.bm25 import BM25
from pod_b.calibration import PROVISIONAL
from pod_b.embeddings import HashingEmbedder
from pod_b.graph import KnowledgeGraph
from pod_b.rerank import LexicalReranker
from pod_b.retriever import HybridRetriever
from pod_b.runtime import load_startup, prune_graph
from pod_b.schemas import ContentUnit
from pod_b.security import RateLimiter
from pod_b.store import DEFAULT_GRAPH, CorpusStore

from .conftest import make_settings
from .fakes import FakeLLM

STRICT, PERM = PROVISIONAL["hash:512|lexical"]


def new_unit(uid, text, source="New_Notes", page=1):
    return {"unit_id": uid, "source_id": source, "source_type": "pdf", "location": {"page": page}, "text": text}


def build_app(tmp_path, llm=None, **settings_kw):
    """App over the mock corpus with hermetic components and an isolated cache dir."""
    settings = make_settings(cache_dir=tmp_path / "cache", embedding_provider="hash", rerank_provider="lexical",
                             **settings_kw)
    store = CorpusStore.from_json()
    graph = KnowledgeGraph.load(DEFAULT_GRAPH)
    idf = BM25([u.searchable_text() for u in store.all()])._idf
    retriever = HybridRetriever(store, HashingEmbedder(), LexicalReranker(idf), 20, graph=graph)
    answerer = GroundedAnswerer(retriever, graph, llm, threshold_strict=STRICT, threshold_permissive=PERM)
    app = create_app(store, retriever, graph, answerer, settings=settings, persist=True)
    return app, TestClient(app), settings


# ---- live ingest -----------------------------------------------------------------------------
def test_ingested_units_are_searchable_tagged_and_versioned(tmp_path):
    app, c, _ = build_app(tmp_path)
    v0 = c.get("/pod-b/health").json()
    r = c.post("/pod-b/ingest/units", json={"units": [
        new_unit("nw-1", "Dropout randomly disables neurons during training to prevent overfitting.", page=3),
        new_unit("nw-2", "Weight decay adds a penalty on large weights to the loss function.", page=4)]})
    assert r.status_code == 200
    body = r.json()
    assert body["ingested"] == 2 and body["total_units"] == v0["units"] + 2 and body["version"] == v0["version"] + 1
    assert body["graph_stale"] is True and body["units_without_concept_evidence"] >= 2  # new units have no concept yet
    assert body["tagging"]["untagged"] == [] or set(body["tagging"]["untagged"]) <= {"nw-1", "nw-2"}
    hit = c.get("/pod-b/search", params={"q": "dropout disables neurons", "k": 1}).json()[0]
    assert hit["unit_id"] == "nw-1" and hit["citation"]["open_url"] == "/sources/New_Notes#page=3"
    ans = c.post("/pod-b/ask", json={"question": "what does dropout do"}).json()
    assert ans["status"] == "grounded" and ans["sources"][0]["unit_id"] == "nw-1"


def test_pod_a_embeddings_and_tags_are_ignored(tmp_path):
    app, c, _ = build_app(tmp_path)
    u = new_unit("nw-9", "Batch normalisation rescales layer inputs.")
    u.update(embedding=[0.1, 0.2], topic_ids=["bogus"], concept_ids=["bogus"])
    assert c.post("/pod-b/ingest/units", json={"units": [u]}).status_code == 200
    stored = app.state.runtime.bundle.store.get("nw-9")
    assert stored.embedding is None and "bogus" not in stored.topic_ids + stored.concept_ids


def test_reingesting_a_source_replaces_it_and_prunes_graph_evidence(tmp_path):
    app, c, _ = build_app(tmp_path)
    before = c.get("/pod-b/coverage").json()
    r = c.post("/pod-b/ingest/units", json={"units": [
        {"unit_id": "sl-03", "source_id": "ML_Slides_L2", "source_type": "slides", "location": {"slide": 3},
         "text": "A derivative measures the instantaneous rate of change of a function."}]}).json()
    assert r["total_units"] == before["units"] - 15 + 1  # the old 15 slide units are gone
    assert r["graph_pruned"]["concept_evidence_removed"] > 0
    cov = c.get("/pod-b/coverage").json()
    assert cov["integrity_problems"] == [] and "c-derivative-rules" in cov["concepts_without_evidence"]
    assert c.get("/pod-b/units/sl-14").status_code == 404  # replaced away


def test_ingest_validation_and_conflicts(tmp_path):
    _, c, _ = build_app(tmp_path)
    assert c.post("/pod-b/ingest/units", json={"units": []}).status_code == 422
    conflict = new_unit("sl-08", "x text", source="Other_Source")  # id belongs to ML_Slides_L2
    assert "already used" in c.post("/pod-b/ingest/units", json={"units": [conflict]}).json()["detail"]
    dup = [new_unit("d1", "one"), new_unit("d1", "two")]
    assert c.post("/pod-b/ingest/units", json={"units": dup}).status_code == 422
    bad = new_unit("b1", "text")
    bad["source_type"] = "slides"  # location is a page anchor
    assert c.post("/pod-b/ingest/units", json={"units": [bad]}).status_code == 422
    nr = {"units": [new_unit("sl-08", "again", source="ML_Slides_L2")], "replace_sources": False}
    assert "already exists" in c.post("/pod-b/ingest/units", json=nr).json()["detail"]


def test_ingest_persists_and_a_restart_serves_it(tmp_path):
    app, c, settings = build_app(tmp_path)
    c.post("/pod-b/ingest/units", json={"units": [new_unit("nw-1", "Dropout randomly disables neurons.")]})
    store, graph = load_startup(settings)  # what a fresh process would load
    assert store.get("nw-1") is not None and store.get("sl-08") is not None
    assert graph.integrity_problems(store) == []


def test_non_demo_corpus_does_not_get_the_demo_graph(tmp_path, monkeypatch):
    settings = make_settings(cache_dir=tmp_path / "cache")
    CorpusStore([ContentUnit.model_validate(new_unit("z1", "Photosynthesis converts light to chemical energy."))]
                ).save_json(tmp_path / "cache" / "ingested_corpus.json")
    store, graph = load_startup(settings)
    assert len(store) == 1 and len(graph.concepts) == 0  # the demo graph only fits the demo corpus


def test_store_save_json_roundtrip_drops_embeddings_and_tags(tmp_path):
    u = ContentUnit.model_validate({**new_unit("a", "text"), "embedding": [1.0], "topic_ids": ["t"]})
    CorpusStore([u]).save_json(tmp_path / "c.json")
    back = CorpusStore.from_json(tmp_path / "c.json").get("a")
    assert back.text == "text" and back.embedding is None and back.topic_ids == []


def test_prune_graph_removes_dangling_evidence():
    g = KnowledgeGraph.load(DEFAULT_GRAPH)
    store = CorpusStore([u for u in CorpusStore.from_json().all() if u.unit_id != "sl-08"])
    prune_graph(g, store)
    assert "sl-08" not in g.concepts["c-chain-rule"].evidence_units and g.integrity_problems(store) == []


def test_reads_stay_consistent_while_ingesting(tmp_path):
    app, c, _ = build_app(tmp_path)
    errors, stop = [], threading.Event()

    def reader():
        while not stop.is_set():
            try:
                assert c.get("/pod-b/search", params={"q": "chain rule", "k": 3}).status_code == 200
                assert c.get("/pod-b/coverage").json()["integrity_problems"] == []
            except Exception as e:  # noqa: BLE001
                errors.append(repr(e))
                return

    ts = [threading.Thread(target=reader) for _ in range(3)]
    [t.start() for t in ts]
    for i in range(4):
        assert c.post("/pod-b/ingest/units", json={"units": [new_unit(f"n{i}", f"extra note number {i} about momentum", page=i + 1)]}).status_code == 200
    stop.set()
    [t.join() for t in ts]
    assert errors == []


# ---- admin guard ---------------------------------------------------------------------------------
def test_admin_token_protects_state_changing_endpoints_only(tmp_path):
    _, c, _ = build_app(tmp_path, admin_token="s3cret")
    body = {"units": [new_unit("nw-1", "Dropout randomly disables neurons.")]}
    assert c.post("/pod-b/ingest/units", json=body).status_code == 401
    assert c.post("/pod-b/ingest/units", json=body, headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert c.post("/pod-b/graph/rebuild").status_code == 401
    assert c.post("/pod-b/ingest/units", json=body, headers={"X-Admin-Token": "s3cret"}).status_code == 200
    assert c.get("/pod-b/search", params={"q": "chain rule"}).status_code == 200  # reads stay open
    assert c.get("/pod-b/health").json()["admin_protected"] is True


# ---- rate limiting ----------------------------------------------------------------------------------
def test_rate_limiter_window_with_fake_clock():
    now = [0.0]
    rl = RateLimiter(2, 60, clock=lambda: now[0])
    rl.check("a"); rl.check("a")
    with pytest.raises(HTTPException) as e:
        rl.check("a")
    assert e.value.status_code == 429 and int(e.value.headers["Retry-After"]) >= 1
    rl.check("b")  # other clients unaffected
    now[0] = 61
    rl.check("a")  # window slid
    RateLimiter(0).check("x")  # 0 disables


def test_ask_is_rate_limited_but_search_is_not(tmp_path):
    _, c, _ = build_app(tmp_path, rate_limit_per_min=3)
    codes = [c.post("/pod-b/ask", json={"question": "what is the chain rule"}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    assert all(c.get("/pod-b/search", params={"q": "chain rule"}).status_code == 200 for _ in range(6))


# ---- graph rebuild ---------------------------------------------------------------------------------------
def test_rebuild_without_llm_is_503(tmp_path):
    _, c, _ = build_app(tmp_path, llm=None)
    r = c.post("/pod-b/graph/rebuild")
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["detail"]


def test_rebuild_swaps_in_the_new_graph_and_persists(tmp_path):
    app, c, settings = build_app(tmp_path, llm=FakeLLM(noise=False))
    c.post("/pod-b/ingest/units", json={"units": [new_unit("nw-1", "Dropout randomly disables neurons.")]})
    v = app.state.runtime.bundle.version
    st = app.state.runtime.start_graph_rebuild(background=False)
    assert st["state"] == "done" and st["concepts"] == 14 and st["integrity_problems"] == []
    assert app.state.runtime.bundle.version == v + 1
    assert c.get("/pod-b/graph/status").json()["state"] == "done"
    assert KnowledgeGraph.load(settings.cache_dir / "graph.json").concepts  # persisted for restart


def test_rebuild_endpoint_runs_in_background(tmp_path):
    _, c, _ = build_app(tmp_path, llm=FakeLLM(noise=False))
    assert c.post("/pod-b/graph/rebuild").status_code == 202
    for _ in range(100):
        if c.get("/pod-b/graph/status").json()["state"] != "running":
            break
        time.sleep(0.05)
    assert c.get("/pod-b/graph/status").json()["state"] == "done"


def test_second_rebuild_while_running_is_409(tmp_path):
    app, c, _ = build_app(tmp_path, llm=FakeLLM())
    app.state.runtime._rebuild = {"state": "running"}
    assert c.post("/pod-b/graph/rebuild").status_code == 409


def test_corpus_change_during_rebuild_discards_the_result(tmp_path):
    app, c, _ = build_app(tmp_path, llm=None)
    rt = app.state.runtime
    inner = FakeLLM(noise=False)

    class Racing:
        name = "racing"
        done = False

        def generate_json(self, system, prompt):
            if not Racing.done:  # someone ingests while the LLM is "thinking"
                Racing.done = True
                rt.ingest([ContentUnit.model_validate(new_unit("race-1", "late arriving unit"))])
            return inner.generate_json(system, prompt)

    rt._b.answerer.llm = Racing()
    before = rt.bundle.graph
    st = rt.start_graph_rebuild(background=False)
    assert st["state"] == "stale" and rt.bundle.store.get("race-1") is not None
    assert rt.bundle.graph.to_dict() == before.to_dict() or rt.bundle.graph.concepts.keys() == before.concepts.keys()
    assert len(rt.bundle.graph.concepts) == 14  # the stale result was NOT swapped in


def test_failed_rebuild_keeps_the_old_graph(tmp_path):
    class Boom:
        name = "boom"
        def generate_json(self, system, prompt):
            raise RuntimeError("API error 429: quota")
    app, c, _ = build_app(tmp_path, llm=Boom())
    v = app.state.runtime.bundle.version
    st = app.state.runtime.start_graph_rebuild(background=False)
    assert st["state"] == "failed" and "429" in st["error"] and app.state.runtime.bundle.version == v


# ---- CORS / sources ----------------------------------------------------------------------------------------
def test_cors_allows_configured_origin_only(tmp_path):
    _, c, _ = build_app(tmp_path)
    ok = c.options("/pod-b/ask", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = c.options("/pod-b/ask", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_sources_route_serves_files_and_blocks_traversal(tmp_path):
    d = tmp_path / "uploads"
    d.mkdir()
    (d / "deck.pdf").write_bytes(b"%PDF-fake")
    (tmp_path / "secret.txt").write_text("nope")
    _, c, _ = build_app(tmp_path, sources_dir=str(d))
    assert c.get("/sources/deck").content == b"%PDF-fake" and c.get("/sources/deck.pdf").status_code == 200
    assert c.get("/sources/missing").status_code == 404
    assert c.get("/sources/..%2Fsecret.txt").status_code == 404 and c.get("/sources/../secret.txt").status_code == 404


def test_sources_route_absent_when_not_configured(tmp_path):
    _, c, _ = build_app(tmp_path)
    assert c.get("/sources/deck").status_code == 404
