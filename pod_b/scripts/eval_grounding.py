"""Development-time evaluation of retrieval + grounding on the labelled queries in pod_b/golden.py.

    python scripts/eval_grounding.py

Works with no LLM (extractive mode) and, if GEMINI_API_KEY is set, also in generative mode.
These are Pod B's own smoke metrics. The team-level framework evaluation (RAGAS/DeepEval) belongs to Pod D and
should call POST /pod-b/ask, which returns `retrieved` (contexts), `answer`, `sources` for exactly that purpose.

CAVEAT: the labelled set is tiny and written by the same author as the corpus/graph; numbers are optimistic.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pod_b.answer import GroundedAnswerer  # noqa: E402
from pod_b.calibration import load_threshold  # noqa: E402
from pod_b.config import Settings  # noqa: E402
from pod_b.golden import LEXICAL, NEAR_MISS, OFF_MATERIAL, SEMANTIC  # noqa: E402
from pod_b.graph import KnowledgeGraph  # noqa: E402
from pod_b.llm import make_llm  # noqa: E402
from pod_b.retriever import build_retriever  # noqa: E402
from pod_b.schemas import AnswerStatus  # noqa: E402
from pod_b.store import CorpusStore, graph_path  # noqa: E402

s = Settings.from_env()
store = CorpusStore.from_json()
graph = KnowledgeGraph.load(graph_path(s.cache_dir))
retriever = build_retriever(store, s, graph=graph)
strict, perm, calibrated = load_threshold(Path(s.cache_dir) / "calibration.json", retriever.backend_key())
llm, llm_why = make_llm(s)
items = LEXICAL + SEMANTIC


def run(use_llm):
    a = GroundedAnswerer(retriever, graph, llm if use_llm else None, threshold_strict=strict,
                         threshold_permissive=perm, calibrated=calibrated, verify_with_llm=s.verify_with_llm)
    hit1 = hit3 = cit_ok = cit_total = cit_any = prec3 = 0
    answered = 0
    for q, ok in items:
        hits = retriever.search(q, 3)
        ids = [h.unit.unit_id for h in hits]
        hit1 += bool(ids) and ids[0] in ok
        hit3 += any(i in ok for i in ids)
        prec3 += sum(i in ok for i in ids) / 3
        r = a.answer(q)
        if r.status != AnswerStatus.REFUSED:
            answered += 1
            cited = [c.unit_id for c in r.sources]
            cit_total += len(cited)
            cit_ok += sum(i in ok for i in cited)
            cit_any += any(i in ok for i in cited)
    n = len(items)
    refused_off = sum(a.answer(q).status == AnswerStatus.REFUSED for q in OFF_MATERIAL) / len(OFF_MATERIAL)
    nm = [a.answer(q).status for q in NEAR_MISS]
    return {
        "mode": "generative" if use_llm else "extractive",
        "n_in_scope": n, "n_off_topic": len(OFF_MATERIAL), "n_near_miss": len(NEAR_MISS),
        "retrieval_hit@1": round(hit1 / n, 2), "retrieval_hit@3": round(hit3 / n, 2),
        "retrieval_precision@3_strict": round(prec3 / n, 2),
        "in_scope_answered": f"{answered}/{n}",
        "citation_precision": round(cit_ok / cit_total, 2) if cit_total else None,
        "answers_with_a_correct_citation": round(cit_any / answered, 2) if answered else None,
        "off_topic_refusal_rate": round(refused_off, 2),
        "near_miss_not_confidently_grounded": f"{sum(x != AnswerStatus.GROUNDED for x in nm)}/{len(nm)}",
    }


print(f"retrieval: {retriever.backend_key()} | thresholds strict={strict} permissive={perm} calibrated={calibrated}")
results = [run(False)]
if llm is not None:
    print(f"LLM available: {llm.name} ({llm_why}) - running generative mode too")
    results.append(run(True))
else:
    print(f"No LLM ({llm_why}): generative mode skipped.")
for r in results:
    print(json.dumps(r, indent=2))
out = Path("eval_results")
out.mkdir(exist_ok=True)
(out / "grounding_dev_eval.json").write_text(json.dumps({"backend": retriever.backend_key(), "results": results}, indent=2))
print("saved -> eval_results/grounding_dev_eval.json")
