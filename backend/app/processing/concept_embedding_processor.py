from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.embeddings.embedding_service import (
    embedding_service
)


def build_concept_embedding_text(
    name: str,
    topic: str | None,
    subtopic: str | None
) -> str:

    parts = [
        f"Concept: {name}"
    ]

    if topic:
        parts.append(
            f"Topic: {topic}"
        )

    if subtopic:
        parts.append(
            f"Subtopic: {subtopic}"
        )

    return "\n".join(parts)


def embed_concepts(
    registry: ConceptRegistry
) -> ConceptRegistry:

    concepts = registry.get_all_concepts()

    texts = []


    for concept in concepts:

        texts.append(
            build_concept_embedding_text(
                name=concept.name,
                topic=concept.topic,
                subtopic=concept.subtopic
            )
        )


    if not texts:
        return registry


    print(
        f"[Embeddings] Encoding "
        f"{len(concepts)} concepts..."
    )


    vectors = embedding_service.encode_batch(
        texts
    )


    for concept, vector in zip(
        concepts,
        vectors
    ):

        concept.embedding = vector


    return registry