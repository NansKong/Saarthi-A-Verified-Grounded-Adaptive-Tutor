import uuid

from qdrant_client.models import (
    PointStruct
)

from app.knowledge.concept_registry import (
    ConceptRecord,
    ConceptRegistry
)

from app.embeddings.embedding_service import (
    embedding_service
)

from app.processing.concept_embedding_processor import (
    build_concept_embedding_text
)

from app.vectorstore.qdrant_service import (
    qdrant_service,
    CONCEPT_COLLECTION
)


def concept_to_payload(
    concept: ConceptRecord
) -> dict:

    return {
        "concept_id":
            concept.concept_id,

        "name":
            concept.name,

        "aliases":
            concept.aliases,

        "topic":
            concept.topic,

        "subtopic":
            concept.subtopic,

        "evidence_units":
            concept.evidence_units,

        "prerequisites":
            concept.prerequisites
    }


def store_concept(
    concept: ConceptRecord
):

    text = build_concept_embedding_text(
        name=concept.name,
        topic=concept.topic,
        subtopic=concept.subtopic
    )


    vector = embedding_service.encode(
        text
    )


    concept.embedding = vector


    point_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"saarthi-concept:{concept.concept_id}"
        )
    )


    point = PointStruct(
        id=point_id,
        vector=vector,
        payload=concept_to_payload(
            concept
        )
    )


    qdrant_service.client.upsert(
        collection_name=CONCEPT_COLLECTION,
        points=[point]
    )


def store_concepts(
    registry: ConceptRegistry
):

    concepts = registry.get_all_concepts()


    if not concepts:
        return


    texts = [

        build_concept_embedding_text(
            name=concept.name,
            topic=concept.topic,
            subtopic=concept.subtopic
        )

        for concept in concepts
    ]


    print(
        f"[Concept Store] Embedding "
        f"{len(concepts)} concepts..."
    )


    vectors = (
        embedding_service.encode_batch(
            texts
        )
    )


    points = []


    for concept, vector in zip(
        concepts,
        vectors
    ):

        concept.embedding = vector


        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"saarthi-concept:{concept.concept_id}"
            )
        )


        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=concept_to_payload(
                    concept
                )
            )
        )


    qdrant_service.client.upsert(
        collection_name=CONCEPT_COLLECTION,
        points=points
    )


    print(
        f"[Concept Store] Stored "
        f"{len(points)} concepts."
    )