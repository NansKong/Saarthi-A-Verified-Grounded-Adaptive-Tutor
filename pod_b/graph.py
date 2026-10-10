"""Knowledge graph: topics -> concepts -> prerequisite edges, plus the checks that keep it honest.

Rules enforced here (these are what 'validated prerequisite' means):
  * An edge "A requires P" is VALIDATED only with textual evidence from the course material:
      - mention : a unit that explains A also mentions P by name/alias, or
      - order   : P is introduced before A in a shared source AND the proposer was confident (>= 0.8)
    and it is rejected when the material contradicts it (A is introduced before P everywhere, no mention).
  * Only validated edges populate ConceptNode.prerequisites (the field Pod C reads).
  * The edge set is a DAG; cycles are broken by dropping the weakest edge.
  * Every unit ends up tagged with concepts and topics (evidence first, BM25 fallback second).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .bm25 import BM25
from .schemas import ConceptNode, ContentUnit, PrereqEdge, Topic
from .store import CorpusStore
from .text import tokenize

ORDER_MIN_LLM_CONF = 0.8


def _contains_phrase(tokens: list[str], phrase: list[str]) -> bool:
    n = len(phrase)
    return n > 0 and any(tokens[i : i + n] == phrase for i in range(len(tokens) - n + 1))


def _pos(u: ContentUnit) -> float:
    loc = u.location
    return float(loc.page if loc.page is not None else loc.slide if loc.slide is not None else loc.t_start or 0)


def name_key(name: str) -> str:
    return " ".join(tokenize(name, keep_stopwords=True))


class KnowledgeGraph:
    def __init__(self, topics: list[Topic], concepts: list[ConceptNode]):
        self.topics: dict[str, Topic] = {t.topic_id: t for t in topics}
        self.concepts: dict[str, ConceptNode] = {c.concept_id: c for c in concepts}

    # ---------------- navigation ----------------
    def topic_chain(self, topic_id: str) -> list[str]:
        out, seen = [], set()
        while topic_id and topic_id in self.topics and topic_id not in seen:
            out.append(topic_id)
            seen.add(topic_id)
            topic_id = self.topics[topic_id].parent_topic_id or ""
        return out

    def prerequisites_of(self, cid: str, transitive: bool = False) -> list[str]:
        direct = list(self.concepts[cid].prerequisites)
        if not transitive:
            return direct
        out, stack = [], list(direct)
        while stack:
            x = stack.pop()
            if x not in out:
                out.append(x)
                stack.extend(self.concepts[x].prerequisites if x in self.concepts else [])
        return out

    def dependents_of(self, cid: str) -> list[str]:
        return [c.concept_id for c in self.concepts.values() if cid in c.prerequisites]

    def concepts_in_topic(self, topic_id: str) -> list[ConceptNode]:
        return [c for c in self.concepts.values() if topic_id in self.topic_chain(c.topic)]

    def topological_order(self) -> list[str]:
        """Prerequisites first (validated edges only). Raises if a cycle exists."""
        indeg = {c: 0 for c in self.concepts}
        for c in self.concepts.values():
            for p in c.prerequisites:
                if p in indeg:
                    indeg[c.concept_id] += 1
        ready = sorted(c for c, d in indeg.items() if d == 0)
        order = []
        while ready:
            x = ready.pop(0)
            order.append(x)
            for d in sorted(self.dependents_of(x)):
                indeg[d] -= 1
                if indeg[d] == 0:
                    ready.append(d)
        if len(order) != len(self.concepts):
            raise ValueError("prerequisite graph has a cycle")
        return order

    def match_concepts(self, query: str, k: int = 3) -> list[tuple[ConceptNode, float]]:
        """Concepts a query is about: 1.0+ when a concept name/alias appears in the query as a phrase,
        otherwise a partial-overlap score capped at 0.8."""
        q = tokenize(query, keep_stopwords=False)
        qset = set(q)
        scored = []
        for c in self.concepts.values():
            best = 0.0
            for phrase in [c.name, *c.aliases]:
                pt = tokenize(phrase, keep_stopwords=False)
                if not pt:
                    continue
                if _contains_phrase(q, pt):
                    best = max(best, 1.0 + 0.1 * len(pt))
                else:
                    best = max(best, 0.8 * len(qset & set(pt)) / len(pt) if len(qset & set(pt)) else 0.0)
            if best > 0:
                scored.append((c, best))
        return sorted(scored, key=lambda t: -t[1])[:k]

    # ---------------- persistence / export ----------------
    def to_dict(self) -> dict:
        return {"topics": [t.model_dump() for t in self.topics.values()],
                "concepts": [c.model_dump() for c in self.concepts.values()]}

    @classmethod
    def from_dict(cls, d: dict) -> "KnowledgeGraph":
        return cls([Topic.model_validate(t) for t in d["topics"]],
                   [ConceptNode.model_validate(c) for c in d["concepts"]])

    def save(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "KnowledgeGraph":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def viz(self) -> dict:
        """Nodes/edges for a flow-map UI. Edge direction: prerequisite -> dependent (learning order)."""
        return {
            "topics": [t.model_dump() for t in self.topics.values()],
            "nodes": [{"id": c.concept_id, "name": c.name, "topic": c.topic, "units": len(c.evidence_units)}
                      for c in self.concepts.values()],
            "edges": [{"source": e.concept_id, "target": c.concept_id, "confidence": e.confidence,
                       "validated": e.validated, "signals": e.signals}
                      for c in self.concepts.values() for e in c.prerequisite_edges],
        }

    # ---------------- integrity ----------------
    def integrity_problems(self, store: CorpusStore) -> list[str]:
        bad = []
        for c in self.concepts.values():
            if c.topic not in self.topics:
                bad.append(f"{c.concept_id}: unknown topic {c.topic}")
            for u in c.evidence_units:
                if store.get(u) is None:
                    bad.append(f"{c.concept_id}: unknown evidence unit {u}")
            for e in c.prerequisite_edges:
                if e.concept_id not in self.concepts:
                    bad.append(f"{c.concept_id}: edge to unknown concept {e.concept_id}")
            if set(c.prerequisites) != {e.concept_id for e in c.prerequisite_edges if e.validated}:
                bad.append(f"{c.concept_id}: prerequisites != validated edges")
        for t in self.topics.values():
            if t.parent_topic_id and t.parent_topic_id not in self.topics:
                bad.append(f"{t.topic_id}: unknown parent {t.parent_topic_id}")
        try:
            self.topological_order()
        except ValueError:
            bad.append("validated prerequisites contain a cycle")
        return bad


# --------------------------------------------------------------------------- #
# Edge validation, DAG enforcement, tagging
# --------------------------------------------------------------------------- #
def validate_edges(graph: KnowledgeGraph, store: CorpusStore) -> dict:
    """Idempotent: recomputes validated/confidence/signals from the proposer's confidence."""
    first: dict[tuple[str, str], float] = {}  # (concept, source) -> earliest position
    for c in graph.concepts.values():
        for uid in c.evidence_units:
            u = store.get(uid)
            if u:
                k = (c.concept_id, u.source_id)
                first[k] = min(first.get(k, 1e18), _pos(u))
    stats = {"validated": 0, "rejected": 0, "contradicted": 0}
    for c in graph.concepts.values():
        a_units = [u for u in (store.get(x) for x in c.evidence_units) if u]
        a_tokens = {u.unit_id: tokenize(u.searchable_text()) for u in a_units}
        kept = []
        for e in c.prerequisite_edges:
            p = graph.concepts.get(e.concept_id)
            if p is None:
                continue
            if e.llm_confidence is None:
                e.llm_confidence = e.confidence
            phrases = [tokenize(x) for x in [p.name, *p.aliases]]
            mention_units = [uid for uid, toks in a_tokens.items() if any(_contains_phrase(toks, ph) for ph in phrases)]
            earlier = later = 0
            for src in {u.source_id for u in a_units} & {s for (cid, s) in first if cid == p.concept_id}:
                pa, pp = first.get((c.concept_id, src)), first.get((p.concept_id, src))
                if pa is None or pp is None:
                    continue
                earlier += pp < pa
                later += pp > pa
            order_ok = earlier > later
            contradicted = later > earlier and not mention_units
            signals = (["mention"] if mention_units else []) + (["order"] if order_ok else []) + \
                      (["contradicted"] if contradicted else [])
            e.validated = bool(mention_units) or (order_ok and e.llm_confidence >= ORDER_MIN_LLM_CONF)
            e.evidence_units = mention_units
            e.signals = signals
            e.confidence = round(min(1.0, 0.5 * e.llm_confidence + 0.3 * bool(mention_units) + 0.2 * order_ok), 3)
            stats["validated" if e.validated else "rejected"] += 1
            stats["contradicted"] += contradicted
            kept.append(e)
        c.prerequisite_edges = kept
        c.prerequisites = [e.concept_id for e in kept if e.validated]
    return stats


def enforce_dag(graph: KnowledgeGraph) -> list[tuple[str, str]]:
    """Drop the weakest edge of each cycle (over ALL edges, validated or not). Returns removed (concept, prereq)."""
    removed: list[tuple[str, str]] = []

    def find_cycle() -> Optional[list[tuple[str, str]]]:
        color: dict[str, int] = {}
        stack: list[str] = []

        def dfs(n: str) -> Optional[list[tuple[str, str]]]:
            color[n] = 1
            stack.append(n)
            for e in graph.concepts[n].prerequisite_edges:
                m = e.concept_id
                if m not in graph.concepts:
                    continue
                if color.get(m) == 1:
                    cyc = stack[stack.index(m):] + [m]
                    return list(zip(cyc, cyc[1:]))
                if color.get(m) is None:
                    r = dfs(m)
                    if r:
                        return r
            stack.pop()
            color[n] = 2
            return None

        for n in graph.concepts:
            if color.get(n) is None:
                r = dfs(n)
                if r:
                    return r
        return None

    while (cyc := find_cycle()):
        def weight(edge):
            c, p = edge
            e = next(x for x in graph.concepts[c].prerequisite_edges if x.concept_id == p)
            return (e.validated, e.confidence)  # unvalidated and low-confidence go first
        c, p = min(cyc, key=weight)
        node = graph.concepts[c]
        node.prerequisite_edges = [e for e in node.prerequisite_edges if e.concept_id != p]
        node.prerequisites = [x for x in node.prerequisites if x != p]
        removed.append((c, p))
    return removed


def tag_units(graph: KnowledgeGraph, store: CorpusStore, auto_ratio: float = 0.6, auto_max: int = 3) -> dict:
    """Back-fill unit.concept_ids / unit.topic_ids. Evidence tags first; remaining units are matched to
    concepts by BM25 over name+aliases+definition. Returns a coverage report."""
    for u in store.all():
        u.concept_ids, u.topic_ids = [], []

    def add(u: ContentUnit, c: ConceptNode) -> None:
        if c.concept_id not in u.concept_ids:
            u.concept_ids.append(c.concept_id)
        for t in graph.topic_chain(c.topic):
            if t not in u.topic_ids:
                u.topic_ids.append(t)

    for c in graph.concepts.values():
        for uid in c.evidence_units:
            if (u := store.get(uid)):
                add(u, c)
    by_evidence = sum(1 for u in store.all() if u.concept_ids)

    auto: list[str] = []
    concepts = list(graph.concepts.values())
    if concepts:
        bm = BM25([f"{c.name} {' '.join(c.aliases)} {c.definition or ''}" for c in concepts])
        for u in store.all():
            if u.concept_ids:
                continue
            sc = bm.scores(u.searchable_text())
            top = max(sc, default=0.0)
            if top <= 0:
                continue
            for i in sorted(range(len(sc)), key=lambda i: -sc[i])[:auto_max]:
                if sc[i] >= auto_ratio * top:
                    add(u, concepts[i])
            auto.append(u.unit_id)
    untagged = [u.unit_id for u in store.all() if not u.concept_ids]
    return {"units": len(store), "tagged_by_evidence": by_evidence, "auto_tagged": auto, "untagged": untagged,
            "concepts_without_evidence": [c.concept_id for c in concepts if not c.evidence_units]}


# --------------------------------------------------------------------------- #
# Evaluation against a hand-labelled graph
# --------------------------------------------------------------------------- #
def evaluate_graph(pred: KnowledgeGraph, gold: KnowledgeGraph) -> dict:
    def keys(c: ConceptNode) -> set[str]:
        return {name_key(x) for x in [c.name, *c.aliases]}

    gold_idx = {gid: keys(g) for gid, g in gold.concepts.items()}
    p2g: dict[str, str] = {}
    for pid, pc in pred.concepts.items():
        pk = keys(pc)
        for gid, gk in gold_idx.items():
            if pk & gk:
                p2g[pid] = gid
                break
    matched_gold = set(p2g.values())
    gold_edges = {(g.concept_id, p) for g in gold.concepts.values() for p in g.prerequisites}
    pred_edges = {(p2g[c.concept_id], p2g[p]) for c in pred.concepts.values() for p in c.prerequisites
                  if c.concept_id in p2g and p in p2g}
    n_pred_edges = sum(len(c.prerequisites) for c in pred.concepts.values())
    tp = len(gold_edges & pred_edges)
    return {
        "concept_recall": len(matched_gold) / len(gold.concepts) if gold.concepts else 0.0,
        "concept_precision": len(p2g) / len(pred.concepts) if pred.concepts else 0.0,
        "edge_recall": tp / len(gold_edges) if gold_edges else 0.0,
        "edge_precision": tp / n_pred_edges if n_pred_edges else 0.0,
        "gold_concepts": len(gold.concepts), "pred_concepts": len(pred.concepts),
        "gold_edges": len(gold_edges), "pred_edges": n_pred_edges,
    }
