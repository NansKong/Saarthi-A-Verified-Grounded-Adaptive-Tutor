"""Okapi BM25 in pure Python (no dependency). Plenty fast for a course-sized corpus."""
from __future__ import annotations

import math
from collections import Counter

from .text import tokenize


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self._tf = [Counter(tokenize(d)) for d in docs]
        self._len = [sum(tf.values()) for tf in self._tf]
        self._avg = (sum(self._len) / len(docs)) if docs else 0.0
        df: Counter = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        n = len(docs)
        # +1 inside the log keeps IDF positive even for terms in most documents
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for tf, dl in zip(self._tf, self._len):
            s = 0.0
            for t in q:
                f = tf.get(t)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * dl / (self._avg or 1.0))
                s += self._idf.get(t, 0.0) * f * (self.k1 + 1) / denom
            out.append(s)
        return out
