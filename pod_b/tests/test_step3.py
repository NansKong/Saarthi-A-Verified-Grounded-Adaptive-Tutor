import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from pod_b.api import create_app
from pod_b.config import Settings
from pod_b.embeddings import ConfigError
from pod_b.graph import KnowledgeGraph, enforce_dag, evaluate_graph, tag_units, validate_edges
from pod_b.graph_builder import GraphBuilder
from pod_b.llm import GeminiLLM, LLMError, make_llm, parse_json_loose
from pod_b.schemas import PrereqEdge
from pod_b.store import DEFAULT_GRAPH, CorpusStore

from .conftest import make_settings
from .fakes import FakeLLM


# ---- bundled demo graph -------------------------------------------------------
def test_demo_graph_is_consistent(graph, store):
    assert graph.integrity_problems(store) == []
    order = graph.topological_order()
    assert order.index("c-derivative") < order.index("c-chain-rule") < order.index("c-backpropagation")
    assert len(graph.topics) == 7 and len(graph.concepts) == 14


def test_every_demo_edge_is_validated_by_the_material(graph, store):
    stats = validate_edges(graph, store)
    assert stats["rejected"] == 0 and stats["validated"] == 17


def test_validate_edges_is_idempotent(graph, store):
    validate_edges(graph, store)
    first = graph.to_dict()
    validate_edges(graph, store)
    assert graph.to_dict() == first


def _add_edge(graph, concept, requires, conf):
    graph.concepts[concept].prerequisite_edges.append(PrereqEdge(concept_id=requires, confidence=conf))


def test_reverse_edge_is_contradicted_and_rejected(graph, store):
    _add_edge(graph, "c-derivative", "c-chain-rule", 0.95)
    validate_edges(graph, store)
    e = next(e for e in graph.concepts["c-derivative"].prerequisite_edges if e.concept_id == "c-chain-rule")
    assert not e.validated and "contradicted" in e.signals
    assert "c-chain-rule" not in graph.concepts["c-derivative"].prerequisites


def test_edge_without_any_textual_evidence_is_not_validated(graph, store):
    _add_edge(graph, "c-gradient", "c-loss-function", 0.5)  # different sources, no mention
    validate_edges(graph, store)
    e = next(e for e in graph.concepts["c-gradient"].prerequisite_edges if e.concept_id == "c-loss-function")
    assert not e.validated and e.signals == []


def test_order_only_edge_needs_high_proposer_confidence(graph, store):
    _add_edge(graph, "c-training-loop", "c-activation-function", 0.9)  # sl-20 precedes sl-23, no mention
    validate_edges(graph, store)
    hi = next(e for e in graph.concepts["c-training-loop"].prerequisite_edges if e.concept_id == "c-activation-function")
    assert hi.validated and hi.signals == ["order"]
    hi.llm_confidence = 0.5
    validate_edges(graph, store)
    assert not hi.validated


def test_enforce_dag_drops_weakest_edge_in_cycle(graph, store):
    _add_edge(graph, "c-derivative", "c-chain-rule", 0.4)
    validate_edges(graph, store)
    removed = enforce_dag(graph)
    assert removed == [("c-derivative", "c-chain-rule")]
    graph.topological_order()  # no exception


def test_tagging_covers_every_unit_and_includes_topic_ancestors(graph, store):
    rep = tag_units(graph, store)
    assert rep["untagged"] == [] and "vd-0035" in rep["auto_tagged"]
    sl09 = store.get("sl-09")
    assert "c-chain-rule" in sl09.concept_ids and {"t-differentiation", "t-calculus"} <= set(sl09.topic_ids)
    assert store.get("vd-0035").concept_ids  # auto-tagged by BM25 fallback


def test_match_concepts(graph):
    assert graph.match_concepts("what is the chain rule")[0][0].concept_id == "c-chain-rule"
    assert graph.match_concepts("why does my learning rate matter")[0][0].concept_id == "c-learning-rate"
    assert graph.match_concepts("explain quantum computing") == []


def test_prerequisite_navigation(graph):
    assert set(graph.prerequisites_of("c-backpropagation")) == {"c-chain-rule", "c-neural-network", "c-gradient-descent"}
    assert "c-derivative" in graph.prerequisites_of("c-overfitting", transitive=True)
    assert "c-training-loop" in graph.dependents_of("c-backpropagation")


def test_save_load_roundtrip(graph, tmp_path):
    graph.save(tmp_path / "g.json")
    assert KnowledgeGraph.load(tmp_path / "g.json").to_dict() == graph.to_dict()


def test_evaluate_graph(graph):
    perfect = evaluate_graph(graph, KnowledgeGraph.load(DEFAULT_GRAPH))
    assert perfect["concept_recall"] == perfect["edge_recall"] == perfect["edge_precision"] == 1.0
    pruned = KnowledgeGraph.load(DEFAULT_GRAPH)
    del pruned.concepts["c-overfitting"]
    pruned.concepts["c-backpropagation"].prerequisites = []
    r = evaluate_graph(pruned, KnowledgeGraph.load(DEFAULT_GRAPH))
    assert r["concept_recall"] < 1.0 and r["edge_recall"] < 1.0 and r["concept_precision"] == 1.0


# ---- LLM builder pipeline (scripted LLM; tests guard rails, not model quality) ----
def test_builder_pipeline_with_noisy_llm(store):
    fresh = CorpusStore.from_json()
    res = GraphBuilder(FakeLLM(), batch_size=12).build(fresh)
    rep, g = res.report, res.graph
    assert rep["hallucinated_unit_ids"] > 0 and rep["malformed_items"] >= 1
    assert rep["dropped_ungrounded_concepts"] == ["ghost concept"]
    assert rep["unknown_names_in_stage_b"] >= 2 and rep["self_or_duplicate_edges"] == 1
    assert rep["cycle_edges_removed"] == [["c-derivative", "c-chain-rule"]]
    assert rep["integrity_problems"] == [] and rep["tagging"]["untagged"] == []
    assert len(g.concepts) == 14  # case variants and batch splits merged
    gold = KnowledgeGraph.load(DEFAULT_GRAPH)
    ev = evaluate_graph(g, gold)
    assert ev["concept_recall"] == 1.0 and ev["edge_recall"] == 1.0 and ev["edge_precision"] == 1.0


def test_builder_makes_one_stage_b_call_and_batches_by_source(store):
    llm = FakeLLM(noise=False)
    GraphBuilder(llm, batch_size=12).build(CorpusStore.from_json())
    assert llm.calls.count("B") == 1 and llm.calls.count("A") == 4  # slides 15->12+3, pdf 7, video 6


def test_builder_fails_loudly_if_nothing_is_grounded():
    class Empty:
        name = "empty"
        def generate_json(self, system, prompt):
            return {"concepts": [{"name": "x", "unit_ids": ["nope"]}]}
    with pytest.raises(ValueError, match="no grounded concepts"):
        GraphBuilder(Empty()).build(CorpusStore.from_json())


# ---- Gemini adapter (fake transport; NOT a live-API test) -------------------------
def _gem(handler, **kw):
    return GeminiLLM("g-key", client=httpx.Client(transport=httpx.MockTransport(handler)), sleep=lambda s: None, **kw)


def _ok(text):
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})


def test_gemini_request_shape_and_parsing():
    seen = {}

    def handler(req):
        seen.update(path=req.url.path, key=req.headers["x-goog-api-key"], body=json.loads(req.content))
        return _ok('```json\n{"concepts": []}\n```')

    out = _gem(handler).generate_json("sys", "prompt")
    assert out == {"concepts": []}
    assert seen["path"].endswith("/models/gemini-2.5-flash:generateContent") and seen["key"] == "g-key"
    assert seen["body"]["systemInstruction"]["parts"][0]["text"] == "sys"
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_ignores_thought_parts_and_model_override():
    def handler(req):
        assert "gemini-x" in req.url.path
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [
            {"text": "thinking...", "thought": True}, {"text": '{"a": 1}'}]}}]})
    assert _gem(handler, model="gemini-x").generate_json("s", "p") == {"a": 1}


def test_gemini_retries_bad_json_once_then_fails():
    n = {"c": 0}

    def flaky(req):
        n["c"] += 1
        return _ok("not json" if n["c"] == 1 else '{"ok": true}')
    assert _gem(flaky).generate_json("s", "p") == {"ok": True} and n["c"] == 2
    with pytest.raises(LLMError, match="valid JSON"):
        _gem(lambda r: _ok("still not json")).generate_json("s", "p")


def test_gemini_blocked_response_raises_clear_error():
    with pytest.raises(LLMError, match="no candidates"):
        _gem(lambda r: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})).generate_json("s", "p")


def test_parse_json_loose_handles_chatter():
    assert parse_json_loose('Sure! {"a": [1, 2]} hope that helps') == {"a": [1, 2]}


def test_make_llm_selection():
    assert make_llm(make_settings())[0] is None
    llm, why = make_llm(make_settings(gemini_api_key="k"))
    assert llm.name == "gemini:gemini-2.5-flash" and why == "auto -> gemini"
    assert make_llm(make_settings(gemini_api_key="k", llm_provider="none"))[0] is None
    assert make_llm(make_settings(gemini_api_key="k", llm_model="gemini-x"))[0].name == "gemini:gemini-x"
    with pytest.raises(ConfigError):
        make_llm(make_settings(llm_provider="gemini"))
    with pytest.raises(ConfigError):
        make_llm(make_settings(llm_provider="bogus"))


# ---- API -----------------------------------------------------------------------
@pytest.fixture(scope="module")
def client(retriever):
    store = CorpusStore.from_json()  # fresh: create_app back-fills tags
    return TestClient(create_app(store, retriever, KnowledgeGraph.load(DEFAULT_GRAPH)))


def test_graph_endpoint_shape(client):
    g = client.get("/pod-b/graph").json()
    assert len(g["nodes"]) == 14 and len(g["edges"]) == 17 and len(g["topics"]) == 7
    e = next(e for e in g["edges"] if e["target"] == "c-chain-rule")
    assert e["source"] == "c-derivative" and e["validated"] and "mention" in e["signals"]


def test_concept_detail_and_404(client):
    d = client.get("/pod-b/concepts/c-backpropagation").json()
    assert d["topic_chain"] == ["Neural networks", "Training neural networks"]
    assert {p["name"] for p in d["prerequisites"]} == {"chain rule", "neural network", "gradient descent"}
    assert "c-derivative" in d["all_prerequisites"]
    assert client.get("/pod-b/concepts/nope").status_code == 404
    assert client.get("/pod-b/concepts/nope/units").status_code == 404


def test_concept_units_for_question_generation(client):
    units = client.get("/pod-b/concepts/c-learning-rate/units").json()
    assert {u["unit_id"] for u in units} == {"sl-15", "tb-0209", "vd-1085"}
    assert all(u["evidence"] and u["citation"]["open_url"].startswith("/sources/") for u in units)
    related = client.get("/pod-b/concepts/c-chain-rule/units", params={"include_related": True}).json()
    assert len(related) >= 4


def test_concept_search_and_topic_filter(client):
    assert client.get("/pod-b/concepts", params={"q": "what is the chain rule"}).json()[0]["concept_id"] == "c-chain-rule"
    ids = {c["concept_id"] for c in client.get("/pod-b/concepts", params={"topic_id": "t-calculus"}).json()}
    assert {"c-derivative", "c-chain-rule", "c-gradient"} <= ids and "c-backpropagation" not in ids
    assert len(client.get("/pod-b/topics").json()) == 7


def test_coverage_endpoint(client):
    c = client.get("/pod-b/coverage").json()
    assert c["units_with_concepts"] == c["units"] == 28 and c["untagged_units"] == []
    assert c["edges_validated"] == 17 and c["edges_unvalidated"] == 0 and c["integrity_problems"] == []


def test_settings_llm_fields_have_defaults():
    s = Settings(embedding_provider="auto", embedding_model="", rerank_provider="auto", rerank_model="",
                 openai_api_key="", gemini_api_key="", cache_dir=Path("x"), candidate_pool=20)
    assert s.llm_provider == "auto" and s.llm_model == ""
