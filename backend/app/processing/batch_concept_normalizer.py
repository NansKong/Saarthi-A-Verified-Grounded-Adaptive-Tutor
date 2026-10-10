import json
import re

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.concept_extractor import (
    slugify_concept
)

from app.vectorstore.concept_search import (
    search_similar_concepts
)

from app.llm.text_llm import (
    generate_json
)


def _normalize_text(
    value: str
) -> str:

    value = (
        value
        .strip()
        .lower()
    )


    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value
    )


    value = re.sub(
        r"\s+",
        " ",
        value
    )


    return value.strip()


def _singularize_word(
    word: str
) -> str:

    if len(word) <= 3:
        return word


    # Preserve words such as:
    # loss
    # analysis
    # basis
    if word.endswith(
        (
            "ss",
            "us",
            "is"
        )
    ):
        return word


    if (
        word.endswith("ies")
        and len(word) > 4
    ):

        return (
            word[:-3]
            + "y"
        )


    if (
        word.endswith("ses")
        and len(word) > 4
    ):

        return word[:-2]


    if (
        word.endswith("s")
        and not word.endswith("ss")
    ):

        return word[:-1]


    return word


def _lookup_key(
    value: str
) -> str:

    normalized = _normalize_text(
        value
    )


    words = (
        normalized.split()
    )


    words = [
        _singularize_word(
            word
        )
        for word in words
    ]


    return " ".join(
        words
    )


def _find_local_match(
    concept_name: str,
    registry: ConceptRegistry
):
    """
    Exact / alias / singular-plural matching.

    No embeddings.
    No LLM.
    """

    incoming_normalized = (
        _normalize_text(
            concept_name
        )
    )

    incoming_key = (
        _lookup_key(
            concept_name
        )
    )


    for record in (
        registry.get_all_concepts()
    ):

        names = [
            record.name,
            *record.aliases
        ]


        for candidate_name in names:

            if (
                _normalize_text(
                    candidate_name
                )
                == incoming_normalized
            ):

                return record


            if (
                _lookup_key(
                    candidate_name
                )
                == incoming_key
            ):

                print(
                    "[Concept Normalizer] "
                    f"Lexical merge: "
                    f"{concept_name} -> "
                    f"{record.name}"
                )

                return record


    return None


def _retrieve_valid_candidates(
    concept_name: str,
    topic: str | None,
    subtopic: str | None,
    registry: ConceptRegistry,
    top_k: int
) -> list[dict]:

    raw_candidates = (
        search_similar_concepts(
            concept_name=concept_name,
            topic=topic,
            subtopic=subtopic,
            limit=top_k + 5
        )
    )


    candidates = []


    for candidate in raw_candidates:

        concept_id = (
            candidate.get(
                "concept_id"
            )
        )


        if not concept_id:
            continue


        # ---------------------------------------------
        # Important:
        # Qdrant can contain concepts from old runs.
        #
        # Only current registry candidates can be
        # selected by the normalizer.
        # ---------------------------------------------

        record = (
            registry.get_concept(
                concept_id
            )
        )


        if not record:
            continue


        candidates.append(
            {
                "concept_id":
                    record.concept_id,

                "name":
                    record.name,

                "aliases":
                    list(
                        record.aliases
                    ),

                "topic":
                    record.topic,

                "subtopic":
                    record.subtopic,

                "score":
                    candidate.get(
                        "score"
                    )
            }
        )


        if len(candidates) >= top_k:
            break


    return candidates


def resolve_concepts_batch(
    requests: list[dict],
    registry: ConceptRegistry,
    top_k: int = 5
) -> dict[str, dict]:
    """
    Resolve many concepts using:

    1. local exact lookup
    2. local lexical dedup
    3. Qdrant candidate retrieval
    4. ONE LLM call for all ambiguous concepts
    """

    resolved = {}

    ambiguous = []


    # =====================================================
    # First pass — cheap/local work
    # =====================================================

    for request in requests:

        request_id = (
            request["request_id"]
        )

        concept_name = (
            request["concept_name"]
            .strip()
        )

        topic = request.get(
            "topic"
        )

        subtopic = request.get(
            "subtopic"
        )


        local_match = (
            _find_local_match(
                concept_name,
                registry
            )
        )


        if local_match:

            resolved[
                request_id
            ] = {
                "concept_id":
                    local_match.concept_id,

                "canonical_name":
                    local_match.name,

                "is_new":
                    False
            }

            continue


        if not registry.get_all_concepts():

            resolved[
                request_id
            ] = {
                "concept_id":
                    slugify_concept(
                        concept_name
                    ),

                "canonical_name":
                    concept_name,

                "is_new":
                    True
            }

            continue


        candidates = (
            _retrieve_valid_candidates(
                concept_name=concept_name,
                topic=topic,
                subtopic=subtopic,
                registry=registry,
                top_k=top_k
            )
        )


        if not candidates:

            resolved[
                request_id
            ] = {
                "concept_id":
                    slugify_concept(
                        concept_name
                    ),

                "canonical_name":
                    concept_name,

                "is_new":
                    True
            }

            continue


        ambiguous.append(
            {
                "request_id":
                    request_id,

                "concept_name":
                    concept_name,

                "topic":
                    topic,

                "subtopic":
                    subtopic,

                "candidates":
                    candidates
            }
        )


    # =====================================================
    # Nothing ambiguous
    # =====================================================

    if not ambiguous:

        return resolved


    print(
        "[Concept Normalizer] "
        f"Batch resolving "
        f"{len(ambiguous)} ambiguous concept(s)."
    )


    # =====================================================
    # ONE LLM CALL
    # =====================================================

    prompt = f"""
You normalize educational concepts.

You are given multiple NEW concepts.

For each new concept, candidate concepts have already
been retrieved from the knowledge base.

Your task is ONLY to determine whether each new concept
means exactly the same educational concept as one of its
candidate concepts.

Similarity does NOT imply identity.

Examples of SAME concepts:

"Gradient Descent Algorithm"
and
"Gradient Descent"

"Neural Network"
and
"Neural Networks"

"Artificial Neural Network"
and
"ANN"


Examples of DIFFERENT concepts:

"Gradient"
and
"Gradient Descent"

"Learning Rate"
and
"Gradient Descent"

"Linear Regression"
and
"Logistic Regression"


Rules:

- Be conservative.
- Related concepts must remain separate.
- Only choose concept_id values appearing in that
  request's candidate list.
- If there is no exact semantic equivalent, mark it new.
- Do not invent candidate IDs.

REQUESTS:

{json.dumps(ambiguous, indent=2)}


Return ONLY JSON:

{{
    "results": [
        {{
            "request_id": "request-id",

            "match": true,

            "concept_id": "existing_concept_id"
        }},
        {{
            "request_id": "request-id",

            "match": false,

            "canonical_name": "Canonical Concept Name"
        }}
    ]
}}
"""


    response = generate_json(
        prompt=prompt,

        system_prompt=(
            "You conservatively normalize multiple "
            "educational concepts in one batch. "
            "Related concepts are not necessarily "
            "identical. Return valid JSON only."
        )
    )


    response_items = (
        response.get(
            "results",
            []
        )
    )


    response_map = {}


    if isinstance(
        response_items,
        list
    ):

        for item in response_items:

            if not isinstance(
                item,
                dict
            ):
                continue


            request_id = (
                item.get(
                    "request_id"
                )
            )


            if request_id:

                response_map[
                    request_id
                ] = item


    # =====================================================
    # Validate every LLM decision locally
    # =====================================================

    for item in ambiguous:

        request_id = (
            item["request_id"]
        )

        concept_name = (
            item["concept_name"]
        )

        candidates = (
            item["candidates"]
        )


        candidate_ids = {
            candidate[
                "concept_id"
            ]
            for candidate in candidates
        }


        decision = (
            response_map.get(
                request_id,
                {}
            )
        )


        if decision.get(
            "match"
        ):

            concept_id = (
                decision.get(
                    "concept_id"
                )
            )


            if (
                concept_id
                in candidate_ids
            ):

                record = (
                    registry.get_concept(
                        concept_id
                    )
                )


                if record:

                    resolved[
                        request_id
                    ] = {
                        "concept_id":
                            record.concept_id,

                        "canonical_name":
                            record.name,

                        "is_new":
                            False
                    }

                    continue


        canonical_name = (
            decision.get(
                "canonical_name"
            )
            or concept_name
        )


        canonical_name = (
            canonical_name.strip()
        )


        resolved[
            request_id
        ] = {
            "concept_id":
                slugify_concept(
                    canonical_name
                ),

            "canonical_name":
                canonical_name,

            "is_new":
                True
        }


    return resolved