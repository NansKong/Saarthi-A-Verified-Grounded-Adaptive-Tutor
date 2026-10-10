"""Scripted tour of Pod B for the demo video. Runs in-process (no server needed) against whatever backend your
.env selects, in an isolated temp cache so it never touches your real data.

    python scripts/demo.py              # runs straight through
    python scripts/demo.py --pause      # waits for Enter between sections (handy while recording)

With GEMINI_API_KEY set you see generative answers; without, the extractive fallback.
"""
import argparse
import dataclasses
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from pod_b.api import create_app  # noqa: E402
from pod_b.config import Settings  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--pause", action="store_true")
args = ap.parse_args()

settings = dataclasses.replace(Settings.from_env(), cache_dir=Path(tempfile.mkdtemp()), rate_limit_per_min=0)
c = TestClient(create_app(settings=settings))


def section(title):
    if args.pause:
        input("\n[Enter] ")
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def show(r):
    print(f"status={r['status']}  mode={r['mode']}  confidence={r['confidence']}")
    if r.get("standalone_question"):
        print(f"(understood as: {r['standalone_question']!r})")
    if r["answer"]:
        print("\n" + r["answer"])
    for n, s in enumerate(r["sources"], 1):
        print(f"  [{n}] {s['label']:<9} {s['open_url']}\n      \"{s['excerpt'][:110]}...\"")
    if r["outside_knowledge"]:
        print("\nOUTSIDE THE COURSE MATERIAL (not source-backed):", *r["outside_knowledge"], sep="\n  - ")
    if r["message"]:
        print("\n" + r["message"])


h = c.get("/pod-b/health").json()
section("1. The knowledge base")
print(f"{h['units']} units from {len(h['sources'])} sources: {h['sources']}")
print("answer mode:", h["mode"], "| retrieval:", c.get("/pod-b/retrieval/info").json()["embedder"], "+",
      c.get("/pod-b/retrieval/info").json()["reranker"])
cov = c.get("/pod-b/coverage").json()
print(f"{cov['units_with_concepts']}/{cov['units']} units tagged to concepts; {cov['concepts']} concepts; "
      f"{cov['edges_validated']} validated prerequisite links; integrity problems: {cov['integrity_problems'] or 'none'}")

section("2. Topics, concepts and prerequisites (every link checked against the source text)")
g = c.get("/pod-b/graph").json()
tn = {t["topic_id"]: t["name"] for t in g["topics"]}
for t in g["topics"]:
    if t["parent_topic_id"] is None:
        subs = [x["name"] for x in g["topics"] if x["parent_topic_id"] == t["topic_id"]]
        print(f"- {t['name']}" + (f"  (subtopics: {', '.join(subs)})" if subs else ""))
if any(n["id"] == "c-backpropagation" for n in g["nodes"]):
    d = c.get("/pod-b/concepts/c-backpropagation").json()
    print("\nTo understand 'backpropagation' first learn:", ", ".join(p["name"] for p in d["prerequisites"]))
    e = next(e for e in g["edges"] if e["target"] == "c-backpropagation" and e["source"] == "c-chain-rule")
    print(f"  chain rule -> backpropagation: validated={e['validated']} via {e['signals']} confidence={e['confidence']}")

section("3. Grounded answer with exact citations")
show(c.post("/pod-b/ask", json={"question": "what is the chain rule"}).json())

section("4. Using a figure: the answer comes from a diagram's description")
show(c.post("/pod-b/ask", json={"question": "what does the loss surface diagram show for gradient descent"}).json())

section("5. A follow-up question in the same chat")
hist = [{"role": "user", "content": "what is gradient descent"},
        {"role": "assistant", "content": "It minimises a loss by stepping against the gradient."}]
show(c.post("/pod-b/ask", json={"question": "and what happens if the learning rate is too big?", "history": hist}).json())

section("6. Declining what the material does not cover")
for q in ("who won the football world cup", "what is a convolutional neural network"):
    print(f"\n> {q}")
    show(c.post("/pod-b/ask", json={"question": q}).json())

section("7. Same refusal, but the student opts in to outside knowledge (clearly labelled)")
if h["mode"] == "generative":
    show(c.post("/pod-b/ask", json={"question": "who won the football world cup", "allow_outside_knowledge": True}).json())
else:
    print("(skipped: opting in to outside knowledge needs a language model - set GEMINI_API_KEY and rerun)")

section("8. New material arrives while the server is running")
r = c.post("/pod-b/ingest/units", json={"units": [{
    "unit_id": "demo-1", "source_id": "Week3_Notes", "source_type": "pdf", "location": {"page": 2},
    "text": "Dropout is a regularization technique that randomly disables a fraction of neurons during training "
            "so the network cannot rely on any single neuron, which reduces overfitting."}]}).json()
print(f"ingested {r['ingested']} unit -> {r['total_units']} total; graph_stale={r['graph_stale']}")
show(c.post("/pod-b/ask", json={"question": "what is dropout"}).json())
