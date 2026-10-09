from app.embeddings.embedding_service import (
    embedding_service
)

from app.vectorstore.qdrant_service import (
    qdrant_service,
    CONTENT_COLLECTION
)


def search_content(
    query: str,
    limit: int = 5
) -> list[dict]:

    query_vector = embedding_service.encode(
        query
    )

    results = qdrant_service.client.query_points(
        collection_name=CONTENT_COLLECTION,
        query=query_vector,
        limit=limit,
        with_payload=True
    )


    matches = []


    for point in results.points:

        payload = point.payload or {}

        matches.append({
            "score": point.score,

            "unit_id":
                payload.get("unit_id"),

            "source_id":
                payload.get("source_id"),

            "source_type":
                payload.get("source_type"),

            "location":
                payload.get("location"),

            "content_type":
                payload.get("content_type"),

            "text":
                payload.get("text"),

            "visual_description":
                payload.get(
                    "visual_description"
                ),

            "topic":
                payload.get("topic"),

            "subtopic":
                payload.get("subtopic"),

            "concept_ids":
                payload.get(
                    "concept_ids",
                    []
                )
        })


    return matches