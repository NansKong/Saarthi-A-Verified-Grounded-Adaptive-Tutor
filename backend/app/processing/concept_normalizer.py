from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.batch_concept_normalizer import (
    resolve_concepts_batch
)


def resolve_concept(
    concept_name: str,
    topic: str | None,
    subtopic: str | None,
    registry: ConceptRegistry,
    top_k: int = 5
) -> dict:

    request_id = (
        "single_concept"
    )


    results = (
        resolve_concepts_batch(
            requests=[
                {
                    "request_id":
                        request_id,

                    "concept_name":
                        concept_name,

                    "topic":
                        topic,

                    "subtopic":
                        subtopic
                }
            ],

            registry=registry,
            top_k=top_k
        )
    )


    return results[
        request_id
    ]