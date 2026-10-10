import json

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.vectorstore.concept_search import (
    search_similar_concepts
)

from app.llm.text_llm import (
    generate_json
)


def extract_prerequisites_for_concept(
    concept_id: str,
    registry: ConceptRegistry,
    top_k: int = 10
) -> list[str]:

    target = registry.get_concept(
        concept_id
    )

    if not target:
        return []


    # -------------------------------------------------
    # STEP 1 — Retrieve semantically related concepts
    # -------------------------------------------------

    candidates = search_similar_concepts(
        concept_name=target.name,
        topic=target.topic,
        subtopic=target.subtopic,
        limit=top_k + 5
    )


    # -------------------------------------------------
    # STEP 2 — Remove stale / invalid candidates
    # -------------------------------------------------

    filtered_candidates = []


    for candidate in candidates:

        candidate_id = candidate.get(
            "concept_id"
        )


        if not candidate_id:
            continue


        # Skip the target itself
        if candidate_id == target.concept_id:
            continue


        # Qdrant may contain concepts from previous
        # executions. Only use concepts present in
        # the active registry.
        candidate_record = registry.get_concept(
            candidate_id
        )


        if not candidate_record:

            print(
                f"[Prerequisite Extractor] "
                f"Skipping stale Qdrant concept: "
                f"{candidate_id}"
            )

            continue


        filtered_candidates.append(
            candidate
        )


        if len(filtered_candidates) >= top_k:
            break


    if not filtered_candidates:
        return []


    # -------------------------------------------------
    # STEP 3 — Build reasoning prompt
    # -------------------------------------------------

    prompt = f"""
You are building a prerequisite graph for an
educational tutoring system.

TARGET CONCEPT:

ID:
{target.concept_id}

NAME:
{target.name}

TOPIC:
{target.topic}

SUBTOPIC:
{target.subtopic}


SEMANTICALLY RELATED CANDIDATES:

{json.dumps(filtered_candidates, indent=2)}


Determine which candidate concepts are genuine
DIRECT prerequisites for understanding the target.

A prerequisite means that a learner should reasonably
understand the candidate concept BEFORE learning the
target concept.

Important:

Semantic similarity does NOT mean prerequisite.

Examples:

"Gradient"
may be a prerequisite for
"Gradient Descent".

But:

"Gradient Descent"
is not automatically a prerequisite for
"Gradient".

"Linear Regression"
and
"Logistic Regression"
are related concepts, but one is not necessarily
a prerequisite for the other.

Rules:

- Select ONLY from the supplied candidates.
- Do not invent concepts.
- Do not select the target itself.
- Prefer DIRECT prerequisites.
- Do not include distant background concepts unless
  clearly necessary.
- Related concepts are NOT automatically prerequisites.
- Be conservative.
- Return an empty list if no clear prerequisite exists.

Return ONLY valid JSON.

Required format:

{{
    "prerequisites": [
        "concept_id_1",
        "concept_id_2"
    ]
}}
"""


    system_prompt = (
        "You identify direct educational prerequisite "
        "relationships with high precision. "
        "Semantic similarity alone does not establish a "
        "prerequisite relationship. "
        "Return ONLY valid JSON."
    )


    # -------------------------------------------------
    # STEP 4 — Use provider router
    #
    # Groq is attempted first.
    # Gemini is used automatically if Groq is limited.
    # -------------------------------------------------

    try:

        result = generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    except Exception as exc:

        print(
            f"[Prerequisite Extractor] "
            f"All LLM providers failed for "
            f"{target.name}: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        # Do NOT silently treat this as a successful
        # prerequisite extraction.
        raise


    # -------------------------------------------------
    # STEP 5 — Validate response structure
    # -------------------------------------------------

    prerequisites = result.get(
        "prerequisites",
        []
    )


    if not isinstance(
        prerequisites,
        list
    ):

        print(
            f"[Prerequisite Extractor] "
            f"Invalid prerequisites format "
            f"for {target.name}"
        )

        return []


    # -------------------------------------------------
    # STEP 6 — Validate IDs against retrieved candidates
    # -------------------------------------------------

    candidate_ids = {
        candidate["concept_id"]
        for candidate in filtered_candidates
    }


    valid_prerequisites = []


    for prerequisite_id in prerequisites:

        if not isinstance(
            prerequisite_id,
            str
        ):
            continue


        if prerequisite_id == target.concept_id:
            continue


        if prerequisite_id not in candidate_ids:
            continue


        if prerequisite_id in valid_prerequisites:
            continue


        valid_prerequisites.append(
            prerequisite_id
        )


    return valid_prerequisites