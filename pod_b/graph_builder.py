"""Build a KnowledgeGraph from Pod A's units with an LLM, then validate it.

Stage A (per batch of units): extract concepts, each tied to the unit_ids that explain it.
Merge:    de-duplicate concepts across batches by normalised name/alias.
Stage B (one call over concept names+definitions): topic hierarchy, assignments, prerequisite proposals.
Then:     validate_edges -> enforce_dag -> tag_units  (see graph.py). The LLM proposes; the material decides.

Guard rails: unit_ids the model invents are dropped; concepts left with no real evidence are dropped
(nothing ungrounded enters the graph); unknown concept names in stage B are ignored and counted.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .graph import KnowledgeGraph, enforce_dag, name_key, tag_units, validate_edges
from .llm import LLM
from .schemas import ConceptNode, ContentUnit, PrereqEdge, Topic
from .store import CorpusStore

SYSTEM_A = """You build a study knowledge base from course material (lecture slides, textbook pages, lecture transcripts).
Use ONLY the supplied units. Never add concepts that are not explained in them. Reply with a single JSON object."""

PROMPT_A = """Units (each starts with [unit_id]):

{units}

Extract the key study concepts explained or defined in these units.
Return JSON: {{"concepts": [{{"name": str, "definition": str, "aliases": [str], "unit_ids": [str]}}]}}
Rules:
- name: canonical, singular, lower-case (keep acronyms), e.g. "chain rule", "gradient descent".
- definition: 1-2 sentences using only the units' content.
- aliases: other names/phrasings these units actually use for the concept (can be empty).
- unit_ids: ONLY ids from the list above whose content explains or defines the concept (not mere passing mentions).
- Prefer a few meaningful concepts over many trivial ones; skip administrative content."""

SYSTEM_B = """You organise a course's concepts into topics and prerequisites. Reply with a single JSON object."""

PROMPT_B = """Concepts:

{concepts}

Return JSON:
{{"topics": [{{"name": str, "parent": str or null}}],
  "assignments": [{{"concept": str, "topic": str}}],
  "prerequisites": [{{"concept": str, "requires": str, "confidence": number}}]}}
Rules:
- 3-8 major topics (parent null); add subtopics (parent = a topic name) only where they help.
- Assign every concept to exactly one, the most specific topic. Use only the concept names listed.
- prerequisites: "concept" can only be understood after "requires". Direct dependencies only (no transitive
  shortcuts), no cycles, no self-references, only listed names. confidence is your certainty from 0 to 1."""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "x"


def _pos(u: ContentUnit) -> float:
    loc = u.location
    return float(loc.page if loc.page is not None else loc.slide if loc.slide is not None else loc.t_start or 0)


def _fmt_unit(u: ContentUnit, max_chars: int) -> str:
    text = u.text if len(u.text) <= max_chars else u.text[:max_chars] + "..."
    fig = f" (figure: {u.image_caption[:200]})" if u.image_caption else ""
    return f"[{u.unit_id}] ({u.source_id}, {u.location.label()}) {text}{fig}"


@dataclass
class BuildResult:
    graph: KnowledgeGraph
    report: dict = field(default_factory=dict)


class GraphBuilder:
    def __init__(self, llm: LLM, batch_size: int = 12, max_unit_chars: int = 700):
        self.llm, self.batch_size, self.max_chars = llm, batch_size, max_unit_chars

    # ------------------------------------------------------------------ #
    def _batches(self, store: CorpusStore) -> list[list[ContentUnit]]:
        ordered = sorted(store.all(), key=lambda u: (u.source_id, _pos(u)))
        out: list[list[ContentUnit]] = []
        cur: list[ContentUnit] = []
        for u in ordered:
            if cur and (len(cur) >= self.batch_size or cur[-1].source_id != u.source_id):
                out.append(cur)
                cur = []
            cur.append(u)
        return out + ([cur] if cur else [])

    def _extract(self, store: CorpusStore, rep: dict) -> list[dict]:
        merged: list[dict] = []
        index: dict[str, int] = {}
        valid = {u.unit_id for u in store.all()}
        for batch in self._batches(store):
            raw = self.llm.generate_json(SYSTEM_A, PROMPT_A.format(
                units="\n".join(_fmt_unit(u, self.max_chars) for u in batch)))
            rep["llm_calls"] += 1
            batch_ids = {u.unit_id for u in batch}
            for item in raw.get("concepts", []) if isinstance(raw, dict) else []:
                if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                    rep["malformed_items"] += 1
                    continue
                name = str(item["name"]).strip()
                aliases = [str(a).strip() for a in item.get("aliases", []) if str(a).strip()]
                ids = [i for i in item.get("unit_ids", []) if isinstance(i, str)]
                good = [i for i in ids if i in valid and i in batch_ids]
                rep["hallucinated_unit_ids"] += len(ids) - len(good)
                keys = {name_key(x) for x in [name, *aliases]}
                hit = next((index[k] for k in keys if k in index), None)
                if hit is None:
                    merged.append({"name": name, "definition": str(item.get("definition", "")).strip(),
                                   "aliases": [], "unit_ids": []})
                    hit = len(merged) - 1
                m = merged[hit]
                if name_key(name) != name_key(m["name"]) and name not in m["aliases"]:
                    m["aliases"].append(name)
                m["aliases"] += [a for a in aliases if name_key(a) != name_key(m["name"]) and a not in m["aliases"]]
                m["unit_ids"] += [i for i in good if i not in m["unit_ids"]]
                if not m["definition"]:
                    m["definition"] = str(item.get("definition", "")).strip()
                for k in {name_key(x) for x in [m["name"], *m["aliases"]]}:
                    index.setdefault(k, hit)
        return merged

    # ------------------------------------------------------------------ #
    def build(self, store: CorpusStore) -> BuildResult:
        rep = {"llm_calls": 0, "hallucinated_unit_ids": 0, "malformed_items": 0, "unknown_names_in_stage_b": 0,
               "dropped_ungrounded_concepts": [], "self_or_duplicate_edges": 0}
        raw = self._extract(store, rep)

        grounded = []
        for m in raw:
            if m["unit_ids"]:
                grounded.append(m)
            else:
                rep["dropped_ungrounded_concepts"].append(m["name"])
        if not grounded:
            raise ValueError("no grounded concepts were extracted")

        b = self.llm.generate_json(SYSTEM_B, PROMPT_B.format(
            concepts="\n".join(f"- {m['name']}: {m['definition']}" for m in grounded)))
        rep["llm_calls"] += 1
        b = b if isinstance(b, dict) else {}

        # concept ids (unique slugs)
        ids, used = {}, set()
        for m in grounded:
            base, cid, n = "c-" + _slug(m["name"]), "c-" + _slug(m["name"]), 2
            while cid in used:
                cid, n = f"{base}-{n}", n + 1
            used.add(cid)
            ids[name_key(m["name"])] = cid
        alias_to_cid = {name_key(x): ids[name_key(m["name"])] for m in grounded for x in [m["name"], *m["aliases"]]}

        # topics
        topics: dict[str, Topic] = {}
        name_to_tid: dict[str, str] = {}
        for t in b.get("topics", []):
            if isinstance(t, dict) and str(t.get("name", "")).strip():
                nm = str(t["name"]).strip()
                tid = "t-" + _slug(nm)
                name_to_tid[name_key(nm)] = tid
                topics[tid] = Topic(topic_id=tid, name=nm, parent_topic_id=None)
        for t in b.get("topics", []):
            if isinstance(t, dict) and t.get("parent") and name_key(str(t.get("name", ""))) in name_to_tid:
                pid = name_to_tid.get(name_key(str(t["parent"])))
                tid = name_to_tid[name_key(str(t["name"]))]
                if pid and pid != tid:
                    topics[tid].parent_topic_id = pid
        # break any parent loop the model may have created
        for tid in list(topics):
            seen, cur = set(), tid
            while cur and cur in topics and cur not in seen:
                seen.add(cur)
                cur = topics[cur].parent_topic_id or ""
            if cur in seen and cur:
                topics[tid].parent_topic_id = None

        assign: dict[str, str] = {}
        for a in b.get("assignments", []):
            if isinstance(a, dict):
                cid = alias_to_cid.get(name_key(str(a.get("concept", ""))))
                tid = name_to_tid.get(name_key(str(a.get("topic", ""))))
                if cid and tid:
                    assign[cid] = tid
                else:
                    rep["unknown_names_in_stage_b"] += 1
        if any(ids[name_key(m["name"])] not in assign for m in grounded):
            topics.setdefault("t-general", Topic(topic_id="t-general", name="General"))

        concepts: dict[str, ConceptNode] = {}
        for m in grounded:
            cid = ids[name_key(m["name"])]
            concepts[cid] = ConceptNode(concept_id=cid, name=m["name"], topic=assign.get(cid, "t-general"),
                                        definition=m["definition"] or None, aliases=m["aliases"],
                                        evidence_units=m["unit_ids"])
        for p in b.get("prerequisites", []):
            if not isinstance(p, dict):
                continue
            c = alias_to_cid.get(name_key(str(p.get("concept", ""))))
            r = alias_to_cid.get(name_key(str(p.get("requires", ""))))
            if not c or not r:
                rep["unknown_names_in_stage_b"] += 1
                continue
            if c == r or any(e.concept_id == r for e in concepts[c].prerequisite_edges):
                rep["self_or_duplicate_edges"] += 1
                continue
            try:
                conf = max(0.0, min(1.0, float(p.get("confidence", 0.7))))
            except (TypeError, ValueError):
                conf = 0.7
            concepts[c].prerequisite_edges.append(PrereqEdge(concept_id=r, confidence=conf))

        graph = KnowledgeGraph(list(topics.values()), list(concepts.values()))
        rep["edge_validation"] = validate_edges(graph, store)
        rep["cycle_edges_removed"] = [list(e) for e in enforce_dag(graph)]
        rep["tagging"] = tag_units(graph, store)
        rep["integrity_problems"] = graph.integrity_problems(store)
        rep["concepts"], rep["topics"] = len(graph.concepts), len(graph.topics)
        return BuildResult(graph, rep)
