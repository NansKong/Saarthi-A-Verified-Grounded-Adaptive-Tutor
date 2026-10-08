"""
dedup.py  --  Piece 4: stop the same question appearing twice.

The rubric asks us to "avoid repeated questions across assessments". This file
does that. Before we store a newly generated question, we compare it to every
question we've already got. If it is too close to one of them, we drop it.

Two ways to compare (pick one):

  1. lexical_similarity  -- DEFAULT. Compares the words/letters of the two
     questions. Needs nothing installed, works offline. Good at catching
     questions that are nearly the same wording.

  2. Gemini embeddings    -- the "proper" way. Turns each question into a
     vector and compares meaning, so it also catches paraphrases ("move the
     parameters" vs "update the weights") that lexical misses. Uses the Gemini
     key you already have. Plug it in by passing an embedder (see below).

--- Run it ---
    python dedup.py
"""

import re
import math
import difflib

from src.mock_data import get_questions

DUP_THRESHOLD = 0.80   # >= this similarity  -> treat as a duplicate
GEMINI_EMBED_MODEL = "text-embedding-004"   # update here if the name changes


# ---------- option 1: lexical similarity (default, no dependencies) ----------

def normalize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def lexical_similarity(a, b):
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    seq = difflib.SequenceMatcher(None, a, b).ratio()          # letter-level
    ta, tb = set(a.split()), set(b.split())                    # word-level
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return max(seq, jaccard)


# ---------- option 2: Gemini embeddings (catches paraphrases) ----------

def cosine(u, v):
    dot = sum(x * y for x, y in zip(u, v))
    nu = math.sqrt(sum(x * x for x in u))
    nv = math.sqrt(sum(y * y for y in v))
    return dot / (nu * nv) if nu and nv else 0.0


def make_gemini_embedder(client_tuple):
    """client_tuple is the ('new'|'old', client) pair used in verifier.py."""
    kind, client = client_tuple

    def embed(text):
        if kind == "new":
            result = client.models.embed_content(model=GEMINI_EMBED_MODEL, contents=text)
            return result.embeddings[0].values
        result = client.embed_content(model=GEMINI_EMBED_MODEL, content=text)
        return result["embedding"]

    return embed


# ---------- the shared comparison ----------

def similarity(a, b, embedder=None):
    if embedder is not None:
        return cosine(embedder(a), embedder(b))
    return lexical_similarity(a, b)


def find_duplicate(new_stem, existing_stems, embedder=None, threshold=DUP_THRESHOLD):
    """Return (closest_existing_stem, similarity). Stem is None if it's not a duplicate."""
    best_stem, best_sim = None, 0.0
    for stem in existing_stems:
        s = similarity(new_stem, stem, embedder)
        if s > best_sim:
            best_stem, best_sim = stem, s
    return (best_stem if best_sim >= threshold else None), best_sim


def is_duplicate(new_stem, existing_stems, embedder=None, threshold=DUP_THRESHOLD):
    dup, _ = find_duplicate(new_stem, existing_stems, embedder, threshold)
    return dup is not None


# ---------- demo ----------

def main():
    existing = [q.stem for q in get_questions()]

    print("=" * 60)
    print("PIECE 4  --  De-duplication")
    print("=" * 60)
    print(f"Comparing new questions against {len(existing)} existing ones")
    print(f"Threshold: {DUP_THRESHOLD}")
    print("-" * 60)

    candidates = [
        ("near-identical wording", "What does the derivative of a function measure, roughly?"),
        ("near-identical wording", "What happens if the learning rate is too large, in practice?"),
        ("paraphrase", "Which calculus tool does backpropagation mainly rely on?"),
        ("fresh question", "Explain the difference between supervised and unsupervised learning."),
    ]

    for label, stem in candidates:
        dup, sim = find_duplicate(stem, existing)
        verdict = "DROP" if dup else "KEEP"
        print(f"[{verdict}]  sim={sim:.2f}  ({label})")
        print(f"        {stem}")
        if dup:
            print(f"        too close to: {dup}")

    print("-" * 60)
    print("Note: lexical similarity caught the re-wordings but NOT the paraphrase")
    print("(same meaning, different words). That is exactly why the embedding")
    print("option exists -- pass a Gemini embedder and it catches those too.")

    print("-" * 60)
    print("Done. The last two pieces of the pod are the misconception report")
    print("and wiring this whole flow into the FastAPI service.")


if __name__ == "__main__":
    main()
