from app.schemas.content_unit import ContentUnit

from app.embeddings.embedding_service import (
    embedding_service
)


def build_embedding_text(
    unit: ContentUnit
) -> str:

    parts = []


    if unit.topic:
        parts.append(
            f"Topic: {unit.topic}"
        )


    if unit.subtopic:
        parts.append(
            f"Subtopic: {unit.subtopic}"
        )


    if unit.concept_ids:

        readable_concepts = [
            concept_id.replace("_", " ")
            for concept_id in unit.concept_ids
        ]

        parts.append(
            "Concepts: "
            +
            ", ".join(readable_concepts)
        )


    if unit.text and unit.text.strip():

        parts.append(
            f"Content: {unit.text.strip()}"
        )


    if (
        unit.visual_description
        and unit.visual_description.strip()
    ):

        parts.append(
            "Visual Description: "
            +
            unit.visual_description.strip()
        )


    return "\n".join(parts)


def embed_content_unit(
    unit: ContentUnit
) -> ContentUnit:

    embedding_text = build_embedding_text(
        unit
    )

    if not embedding_text.strip():
        return unit


    unit.embedding = (
        embedding_service.encode(
            embedding_text
        )
    )

    return unit

def embed_content_units(
    units: list[ContentUnit]
) -> list[ContentUnit]:

    valid_units = []
    embedding_texts = []


    for unit in units:

        text = build_embedding_text(
            unit
        )

        if not text.strip():
            continue

        valid_units.append(
            unit
        )

        embedding_texts.append(
            text
        )


    if not embedding_texts:
        return units


    print(
        f"[Embeddings] Encoding "
        f"{len(embedding_texts)} content units..."
    )


    vectors = embedding_service.encode_batch(
        embedding_texts
    )


    for unit, vector in zip(
        valid_units,
        vectors
    ):

        unit.embedding = vector


    return units