"""Build the concept graph from your corpus with the configured LLM (Gemini).

    python scripts/build_graph.py                       # mock corpus -> .pod_b_cache/graph.json
    POD_B_CORPUS=units.json python scripts/build_graph.py

On the bundled mock corpus it also scores the result against the hand-labelled graph
(concept/edge precision and recall) - a real measurement of the LLM extractor.
The API picks up .pod_b_cache/graph.json automatically on next start.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pod_b.config import Settings  # noqa: E402
from pod_b.graph import KnowledgeGraph, evaluate_graph  # noqa: E402
from pod_b.graph_builder import GraphBuilder  # noqa: E402
from pod_b.llm import make_llm  # noqa: E402
from pod_b.store import DEFAULT_GRAPH, CorpusStore, corpus_path, DEFAULT_CORPUS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", type=Path, help="where to write the graph (default: <cache>/graph.json)")
ap.add_argument("--batch-size", type=int, default=12)
args = ap.parse_args()

s = Settings.from_env()
llm, why = make_llm(s)
if llm is None:
    sys.exit(f"No LLM configured ({why}). Set GEMINI_API_KEY in .env, then run scripts/check_gemini.py first.")

store = CorpusStore.from_json()
print(f"LLM: {llm.name} ({why}) | corpus: {corpus_path()} | units: {len(store)}")
res = GraphBuilder(llm, batch_size=args.batch_size).build(store)
out = args.out or Path(s.cache_dir) / "graph.json"
res.graph.save(out)
(Path(out).with_suffix(".report.json")).write_text(json.dumps(res.report, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in res.report.items() if k != "tagging"}, indent=2))
t = res.report["tagging"]
print(f"tagging: {t['tagged_by_evidence']}/{t['units']} by evidence, {len(t['auto_tagged'])} auto, {len(t['untagged'])} untagged")
if Path(corpus_path()) == DEFAULT_CORPUS:
    ev = evaluate_graph(res.graph, KnowledgeGraph.load(DEFAULT_GRAPH))
    print("vs hand-labelled graph:", json.dumps({k: round(v, 2) if isinstance(v, float) else v for k, v in ev.items()}))
print(f"saved -> {out}")
