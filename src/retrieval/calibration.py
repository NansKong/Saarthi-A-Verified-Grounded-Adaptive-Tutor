"""Refusal-threshold calibration. Reranker scores are not comparable across backends (lexical coverage vs
cross-encoder sigmoid), so the 'is this covered?' threshold is stored per backend and measured, not guessed."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

# (strict, permissive). Measured on 20 in-scope / 10 off-topic queries over the mock corpus: tiny sample, so provisional.
PROVISIONAL = {"hash:512|lexical": (0.42, 0.21)}
PROVISIONAL_OTHER = (0.30, 0.10)  # unmeasured backend: guesses, flagged as uncalibrated - run scripts/calibrate.py


def calibrate(in_scope: list[float], off_scope: list[float]) -> dict:
    """Two thresholds, because the two answer modes fail differently:
      threshold            STRICT  - best balanced accuracy; used when nothing downstream can catch a bad pass
                                      (extractive mode, no LLM). Ties: widest gap, then lower threshold.
      threshold_permissive PERMISSIVE - 0.8 x the lowest in-scope score; used when an LLM judge follows, because a
                                      false refusal is final while a false pass is still caught by the LLM."""
    vals = sorted(set(in_scope) | set(off_scope))
    cands = [vals[0] - 1e-6] + [(a + b) / 2 for a, b in zip(vals, vals[1:])] + [vals[-1] + 1e-6]
    best = None
    for t in cands:
        tpr = sum(v >= t for v in in_scope) / len(in_scope)
        tnr = sum(v < t for v in off_scope) / len(off_scope)
        lo = max([v for v in vals if v < t], default=t)
        hi = min([v for v in vals if v >= t], default=t)
        key = ((tpr + tnr) / 2, hi - lo, -t)
        if best is None or key > best[0]:
            best = (key, t, tpr, tnr)
    (ba, gap, _), t, tpr, tnr = best
    return {"threshold": round(t, 4), "threshold_permissive": round(0.8 * min(in_scope), 4),
            "balanced_accuracy": round(ba, 3), "in_scope_kept": round(tpr, 3),
            "off_scope_refused": round(tnr, 3), "in_scope_min": round(min(in_scope), 3),
            "off_scope_max": round(max(off_scope), 3), "n_in": len(in_scope), "n_off": len(off_scope)}


def load_threshold(path: Path, backend_key: str) -> tuple[float, float, bool]:
    """(strict, permissive, calibrated?)"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if backend_key in data:
            e = data[backend_key]
            return float(e["threshold"]), float(e["threshold_permissive"]), True
    except (OSError, ValueError, KeyError):
        pass
    return (*PROVISIONAL.get(backend_key, PROVISIONAL_OTHER), False)


def save_calibration(path: Path, backend_key: str, result: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data[backend_key] = result
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def top_relevances(retriever, queries: Iterable[str]) -> list[float]:
    out = []
    for q in queries:
        hits = retriever.search(q, 1)
        out.append(hits[0].relevance if hits else 0.0)
    return out
