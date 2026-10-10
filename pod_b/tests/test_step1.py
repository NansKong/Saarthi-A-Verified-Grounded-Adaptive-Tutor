import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from pod_b.api import create_app
from pod_b.schemas import (ContentUnit, Location, make_citation)
from pod_b.store import CorpusStore


# ---- Location ---------------------------------------------------------------
def test_location_requires_exactly_one_anchor():
    with pytest.raises(ValidationError):
        Location()
    with pytest.raises(ValidationError):
        Location(page=1, slide=2)


def test_location_rejects_bad_video_range():
    with pytest.raises(ValidationError):
        Location(t_start=100, t_end=50)
    with pytest.raises(ValidationError):
        Location(page=3, t_end=10)


@pytest.mark.parametrize(
    "loc,label,url",
    [
        (Location(slide=14), "Slide 14", "/sources/S#slide=14"),
        (Location(page=212), "p. 212", "/sources/S#page=212"),
        (Location(t_start=761), "@12:41", "/sources/S?t=761"),
        (Location(t_start=3725), "@1:02:05", "/sources/S?t=3725"),
    ],
)
def test_label_and_open_url(loc, label, url):
    assert loc.label() == label
    assert loc.open_url("S") == url


# ---- ContentUnit ------------------------------------------------------------
def test_source_type_must_match_location():
    with pytest.raises(ValidationError):
        ContentUnit(unit_id="x", source_id="s", source_type="pdf",
                    location=Location(slide=1), text="hello")


def test_searchable_text_includes_caption():
    u = ContentUnit(unit_id="x", source_id="s", source_type="slides",
                    location=Location(slide=1), text="body", image_caption="a bowl-shaped surface")
    assert "bowl-shaped" in u.searchable_text()


def test_make_citation_derives_from_unit():
    u = ContentUnit(unit_id="x", source_id="deck", source_type="slides",
                    location=Location(slide=14), text="t" * 500)
    c = make_citation(u)
    assert c.label == "Slide 14" and c.open_url == "/sources/deck#slide=14"
    assert len(c.excerpt) == 300


# ---- Mock corpus ------------------------------------------------------------
def test_mock_corpus_loads_and_covers_all_modalities(store):
    assert len(store) >= 25
    assert set(store.sources().values()) == {"video", "pdf", "slides"}


def test_mock_corpus_has_figure_captions(store):
    assert any(u.image_caption for u in store.all())


def test_duplicate_ids_rejected(store):
    u = store.all()[0]
    with pytest.raises(ValueError):
        CorpusStore([u, u])


def test_corpus_does_not_cover_quantum_computing(store):
    # sanity check for the later refusal demo
    assert not any("quantum" in u.searchable_text().lower() for u in store.all())


# ---- API --------------------------------------------------------------------
@pytest.fixture(scope="module")
def client(store, retriever):
    from pod_b.graph import KnowledgeGraph
    from pod_b.store import DEFAULT_GRAPH
    return TestClient(create_app(store, retriever, KnowledgeGraph.load(DEFAULT_GRAPH)))


def test_health(client):
    r = client.get("/pod-b/health")
    assert r.status_code == 200 and r.json()["units"] == len(CorpusStore.from_json())


def test_list_units_filters_and_paginates(client):
    r = client.get("/pod-b/units", params={"source_id": "ML_Slides_L2", "limit": 3})
    body = r.json()
    assert r.status_code == 200 and len(body) == 3
    assert all(u["source_id"] == "ML_Slides_L2" for u in body)
    assert "embedding" not in body[0]


def test_get_unit_and_404(client):
    body = client.get("/pod-b/units/sl-14").json()
    assert body["location"]["slide"] == 14 and "embedding" not in body
    assert client.get("/pod-b/units/nope").status_code == 404
