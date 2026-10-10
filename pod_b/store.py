"""In-memory corpus store. Step 1 reads Pod A's units from JSON (mock now, real later)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Optional

from .schemas import ContentUnit

DEFAULT_CORPUS = Path(__file__).parent / "mock" / "mock_corpus.json"


def corpus_path() -> Path:
    """POD_B_CORPUS overrides the default so real data slots in without code changes."""
    return Path(os.environ.get("POD_B_CORPUS", DEFAULT_CORPUS))


class CorpusStore:
    def __init__(self, units: Iterable[ContentUnit]):
        self._units: dict[str, ContentUnit] = {}
        for u in units:
            if u.unit_id in self._units:
                raise ValueError(f"duplicate unit_id: {u.unit_id}")
            self._units[u.unit_id] = u

    @classmethod
    def from_json(cls, path: Optional[Path] = None) -> "CorpusStore":
        raw = json.loads(Path(path or corpus_path()).read_text(encoding="utf-8"))
        items = raw["units"] if isinstance(raw, dict) else raw
        return cls(ContentUnit.model_validate(item) for item in items)

    def save_json(self, path: Path) -> None:
        """Persist raw units (no embeddings/tags: Pod B recomputes those)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        units = [u.model_dump(exclude={"embedding", "topic_ids", "concept_ids"}) for u in self._units.values()]
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"course_id": "ingested", "units": units}), encoding="utf-8")
        tmp.replace(path)  # atomic: a crash never leaves a half-written corpus

    def __len__(self) -> int:
        return len(self._units)

    def get(self, unit_id: str) -> Optional[ContentUnit]:
        return self._units.get(unit_id)

    def all(self) -> list[ContentUnit]:
        return list(self._units.values())

    def by_source(self, source_id: str) -> list[ContentUnit]:
        return [u for u in self._units.values() if u.source_id == source_id]

    def sources(self) -> dict[str, str]:
        """source_id -> source_type"""
        return {u.source_id: u.source_type for u in self._units.values()}


DEFAULT_GRAPH = Path(__file__).parent / "mock" / "mock_graph.json"


def graph_path(cache_dir: Path = Path(".pod_b_cache")) -> Path:
    """POD_B_GRAPH wins; else a graph you built (scripts/build_graph.py); else the bundled demo graph."""
    if os.environ.get("POD_B_GRAPH"):
        return Path(os.environ["POD_B_GRAPH"])
    built = Path(cache_dir) / "graph.json"
    return built if built.is_file() else DEFAULT_GRAPH


def startup_corpus_path(cache_dir: Path = Path(".pod_b_cache")) -> Path:
    """POD_B_CORPUS > units ingested through the API (persisted in the cache dir) > bundled mock corpus."""
    if os.environ.get("POD_B_CORPUS"):
        return Path(os.environ["POD_B_CORPUS"])
    ingested = Path(cache_dir) / "ingested_corpus.json"
    return ingested if ingested.is_file() else DEFAULT_CORPUS
