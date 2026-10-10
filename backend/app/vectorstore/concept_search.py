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


def search_similar_concepts(
    concept_name: str,
    topic: str | None = None,
    subtopic: str | None = None,
    limit: int = 5
) -> list[dict]:

    query_text = (
        build_concept_embedding_text(
            name=concept_name,
            topic=topic,
            subtopic=subtopic
        )
    )


    query_vector = (
        embedding_service.encode(
            query_text
        )
    )


    results = (
        qdrant_service.client.query_points(
            collection_name=CONCEPT_COLLECTION,
            query=query_vector,
            limit=limit,
            with_payload=True
        )
    )


    matches = []


    for point in results.points:

        payload = point.payload or {}

        matches.append({
            "score":
                point.score,

            "concept_id":
                payload.get(
                    "concept_id"
                ),

            "name":
                payload.get(
                    "name"
                ),

            "aliases":
                payload.get(
                    "aliases",
                    []
                ),

            "topic":
                payload.get(
                    "topic"
                ),

            "subtopic":
                payload.get(
                    "subtopic"
                )
        })


    return matches