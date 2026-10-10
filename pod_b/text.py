"""Tokenisation shared by BM25, the hashing embedder and the lexical reranker."""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

STOPWORDS = frozenset(
    """a an and are as at be been being but by can could do does did for from had has have how i if in
    into is it its of on or our so such than that the their then there these they this those to was we
    were what when where which who why will with would you your me my about explain tell give show""".split()
)


def stem(tok: str) -> str:
    """Very light suffix stripping so 'computes/computing/computed' and plurals line up."""
    if len(tok) <= 3:
        return tok
    for suf, rep in (("ies", "y"), ("sses", "ss"), ("ing", ""), ("ed", ""), ("ly", ""), ("s", "")):
        if tok.endswith(suf) and not (suf == "s" and tok.endswith("ss")):
            base = tok[: -len(suf)] + rep
            if len(base) >= 3:
                return base
    return tok


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    toks = _WORD.findall(text.lower())
    if not keep_stopwords:
        toks = [t for t in toks if t not in STOPWORDS]
    return [stem(t) for t in toks]
