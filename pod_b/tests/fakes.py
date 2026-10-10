import re

from pod_b.graph import KnowledgeGraph
from pod_b.graph_builder import SYSTEM_A
from pod_b.store import DEFAULT_GRAPH


class FakeLLM:
    """Scripted stand-in for Gemini. Replays the hand-labelled demo graph through the real builder
    pipeline (plus some deliberately bad output) - so tests check the pipeline's guard rails, not model quality."""
    name = "fake"

    def __init__(self, *, noise: bool = True):
        self.gold = KnowledgeGraph.load(DEFAULT_GRAPH)
        self.noise, self.calls = noise, []

    def generate_json(self, system: str, prompt: str) -> dict:
        self.calls.append("A" if system == SYSTEM_A else "B")
        return self._stage_a(prompt) if system == SYSTEM_A else self._stage_b()

    def _stage_a(self, prompt: str) -> dict:
        in_batch = set(re.findall(r"^\[([a-z]+-\d+)\]", prompt, flags=re.M))
        out = []
        for c in self.gold.concepts.values():
            ids = [u for u in c.evidence_units if u in in_batch]
            if ids:
                name = c.name.title() if c.concept_id == "c-chain-rule" else c.name  # case variant must still merge
                if self.noise:
                    ids = ids + ["zz-999"]  # hallucinated id
                out.append({"name": name, "definition": c.definition, "aliases": c.aliases, "unit_ids": ids})
        if self.noise:
            out += [{"definition": "no name"}, "garbage", {"name": "ghost concept", "definition": "x", "unit_ids": ["zz-1"]}]
        return {"concepts": out}

    def _stage_b(self) -> dict:
        g = self.gold
        topics = [{"name": t.name, "parent": g.topics[t.parent_topic_id].name if t.parent_topic_id else None}
                  for t in g.topics.values()]
        assign = [{"concept": c.name, "topic": g.topics[c.topic].name} for c in g.concepts.values()]
        prereq = [{"concept": c.name, "requires": g.concepts[p].name, "confidence": 0.9}
                  for c in g.concepts.values() for p in c.prerequisites]
        if self.noise:
            prereq += [
                {"concept": "derivative", "requires": "chain rule", "confidence": 0.5},  # reverse -> cycle + contradicted
                {"concept": "derivative", "requires": "derivative", "confidence": 1},  # self edge
                {"concept": "chain rule", "requires": "teleportation", "confidence": 1},  # unknown name
            ]
            assign.append({"concept": "nonexistent", "topic": "Calculus"})
        return {"topics": topics, "assignments": assign, "prerequisites": prereq}


class ScriptedLLM:
    """Routes each prompt type to a handler so tests can script one behaviour at a time.
    handlers: answer / verify / standalone / outside -> callable(prompt) -> dict (or raises)."""
    name = "scripted"

    def __init__(self, answer=None, verify=None, standalone=None, outside=None):
        self.h = {"answer": answer, "verify": verify, "standalone": standalone, "outside": outside}
        self.calls = []

    def generate_json(self, system: str, prompt: str) -> dict:
        kind = ("answer" if system.startswith("You are a course tutor") else
                "verify" if "fact checker" in system else
                "standalone" if "rewrite follow-up" in system else
                "outside" if "helpful tutor" in system else "other")
        self.calls.append(kind)
        h = self.h.get(kind)
        if h is None:
            raise AssertionError(f"unexpected LLM call: {kind}")
        return h(prompt)
