import json

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.vectorstore.concept_search import (
    search_similar_concepts
)

from app.llm.text_llm import (
    generate_json,
    LLMUnavailableError
)


def build_candidate_set(
    concept,
    registry: ConceptRegistry,
    top_k: int = 8
) -> list[dict]:
    """
    Retrieve prerequisite candidates for one concept
    using semantic similarity from Qdrant.

    Only concepts that currently exist in the active
    ConceptRegistry are allowed.
    """

    raw_candidates = search_similar_concepts(
        concept_name=concept.name,
        topic=concept.topic,
        subtopic=concept.subtopic,
        limit=top_k + 8
    )


    candidates = []


    for candidate in raw_candidates:

        candidate_id = candidate.get(
            "concept_id"
        )


        if not candidate_id:
            continue


        # Never allow self-edge
        if candidate_id == concept.concept_id:
            continue


        candidate_record = registry.get_concept(
            candidate_id
        )


        # Qdrant can contain stale concepts from
        # previous test runs.
        if not candidate_record:

            print(
                "[Batch Prerequisite] "
                f"Skipping stale concept: "
                f"{candidate_id}"
            )

            continue


        candidates.append(
            {
                "concept_id":
                    candidate_record.concept_id,

                "name":
                    candidate_record.name,

                "topic":
                    candidate_record.topic,

                "subtopic":
                    candidate_record.subtopic
            }
        )


        if len(candidates) >= top_k:
            break


    return candidates


def extract_prerequisites_for_batch(
    concepts: list,
    registry: ConceptRegistry,
    top_k: int = 8
) -> dict[str, list[dict]]:
    """
    Process several target concepts in ONE LLM call.

    Returns:

    {
        "gradient_descent": [
            {
                "prerequisite_id": "gradient",
                "confidence": 0.96
            }
        ]
    }
    """

    batch_payload = []

    allowed_candidates = {}


    # =====================================================
    # Build candidate lists locally
    # =====================================================

    for concept in concepts:

        candidates = build_candidate_set(
            concept=concept,
            registry=registry,
            top_k=top_k
        )


        allowed_candidates[
            concept.concept_id
        ] = {
            candidate["concept_id"]
            for candidate in candidates
        }


        batch_payload.append(
            {
                "target": {
                    "concept_id":
                        concept.concept_id,

                    "name":
                        concept.name,

                    "topic":
                        concept.topic,

                    "subtopic":
                        concept.subtopic
                },

                "candidate_prerequisites":
                    candidates
            }
        )


    # =====================================================
    # If every target has zero candidates, no LLM needed
    # =====================================================

    if not any(
        allowed_candidates.values()
    ):

        return {
            concept.concept_id: []
            for concept in concepts
        }


    # =====================================================
    # ONE prompt for entire batch
    # =====================================================

    prompt = f"""
You are building a high-precision prerequisite knowledge
graph for an adaptive tutoring system.

You will receive MULTIPLE target educational concepts.

Each target contains a small list of candidate concepts
retrieved using semantic similarity.

Your job is to determine which candidates are genuine
DIRECT educational prerequisites.

A DIRECT prerequisite means:

A learner should reasonably understand the prerequisite
concept BEFORE learning the target concept.

IMPORTANT:

Semantic similarity does NOT imply prerequisite.

Two concepts may be strongly related but neither may be
a prerequisite of the other.

Be conservative.

Only include an edge when you are highly confident that
the direction is educationally correct.

Examples:

Gradient -> Gradient Descent
VALID

Neural Network -> Backpropagation
VALID

Linear Regression -> Neural Network
INVALID

Logistic Regression -> Neural Network
INVALID

Gradient Descent -> Learning Rate
INVALID DIRECTION

Machine Learning -> every ML concept
DO NOT automatically assume this.

RULES:

1. Only use candidate IDs supplied for each target.
2. Never invent concept IDs.
3. Never create a self-edge.
4. Only return DIRECT prerequisites.
5. Do not return merely related concepts.
6. Confidence must be between 0 and 1.
7. If there is no clear prerequisite for a target,
   return an empty prerequisite list.
8. Prefer precision over recall.

INPUT BATCH:

{json.dumps(batch_payload, indent=2)}


Return ONLY valid JSON.

Required structure:

{{
    "results": [
        {{
            "target_id": "gradient_descent",
            "prerequisites": [
                {{
                    "prerequisite_id": "gradient",
                    "confidence": 0.96
                }},
                {{
                    "prerequisite_id": "loss_function",
                    "confidence": 0.91
                }}
            ]
        }},
        {{
            "target_id": "another_concept",
            "prerequisites": []
        }}
    ]
}}
"""


    system_prompt = (
        "You generate high-precision DIRECT educational "
        "prerequisite relationships for a tutoring "
        "knowledge graph. "
        "Do not confuse semantic similarity with "
        "prerequisite dependency. "
        "Return only valid JSON."
    )


    # =====================================================
    # Provider router:
    #
    # Groq -> Gemini -> LLMUnavailableError
    # =====================================================

    result = generate_json(
        prompt=prompt,
        system_prompt=system_prompt
    )


    # =====================================================
    # Validate response locally
    # =====================================================

    final_results = {
        concept.concept_id: []
        for concept in concepts
    }


    raw_results = result.get(
        "results",
        []
    )


    if not isinstance(
        raw_results,
        list
    ):

        print(
            "[Batch Prerequisite] "
            "Invalid LLM response format."
        )

        return final_results


    valid_target_ids = {
        concept.concept_id
        for concept in concepts
    }


    for target_result in raw_results:

        if not isinstance(
            target_result,
            dict
        ):
            continue


        target_id = target_result.get(
            "target_id"
        )


        if target_id not in valid_target_ids:
            continue


        prerequisites = target_result.get(
            "prerequisites",
            []
        )


        if not isinstance(
            prerequisites,
            list
        ):
            continue


        seen = set()


        for prerequisite in prerequisites:

            if not isinstance(
                prerequisite,
                dict
            ):
                continue


            prerequisite_id = prerequisite.get(
                "prerequisite_id"
            )


            if not prerequisite_id:
                continue


            # Must have come from this target's
            # candidate set.
            if prerequisite_id not in (
                allowed_candidates.get(
                    target_id,
                    set()
                )
            ):

                continue


            if prerequisite_id == target_id:
                continue


            if prerequisite_id in seen:
                continue


            try:

                confidence = float(
                    prerequisite.get(
                        "confidence",
                        0
                    )
                )


            except (
                TypeError,
                ValueError
            ):

                confidence = 0.0


            # Strict local confidence filter
            if confidence < 0.85:
                continue


            seen.add(
                prerequisite_id
            )


            final_results[
                target_id
            ].append(
                {
                    "prerequisite_id":
                        prerequisite_id,

                    "confidence":
                        confidence
                }
            )


    return final_results