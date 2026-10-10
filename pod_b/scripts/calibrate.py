"""Calibrate the 'is this covered by the material?' thresholds for the CURRENT backend.

    python scripts/calibrate.py            # uses the labelled queries in pod_b/golden.py
    python scripts/calibrate.py --file my_queries.json   # {"in_scope": [...], "off_scope": [...]}

Run again whenever you change embedder/reranker/model, and with queries from YOUR course material - the bundled
set is tiny. Results are stored in .pod_b_cache/calibration.json and picked up by the API automatically.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pod_b.calibration import calibrate, save_calibration, top_relevances  # noqa: E402
from pod_b.config import Settings  # noqa: E402
from pod_b.golden import LEXICAL, OFF_MATERIAL, SEMANTIC  # noqa: E402
from pod_b.graph import KnowledgeGraph  # noqa: E402
from pod_b.retriever import build_retriever  # noqa: E402
from pod_b.store import CorpusStore, graph_path  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=Path)
args = ap.parse_args()

s = Settings.from_env()
store = CorpusStore.from_json()
r = build_retriever(store, s, graph=KnowledgeGraph.load(graph_path(s.cache_dir)))
if args.file:
    d = json.loads(args.file.read_text(encoding="utf-8"))
    ins, offs = d["in_scope"], d["off_scope"]
else:
    ins, offs = [q for q, _ in LEXICAL + SEMANTIC], OFF_MATERIAL
res = calibrate(top_relevances(r, ins), top_relevances(r, offs))
save_calibration(Path(s.cache_dir) / "calibration.json", r.backend_key(), res)
print("backend:", r.backend_key())
print(json.dumps(res, indent=2))
if res["n_in"] < 50 or res["n_off"] < 50:
    print("\nWARNING: fewer than 50 queries per group - treat these thresholds as rough.")
