import uuid

from qdrant_client.models import (
    PointStruct
)

from app.schemas.content_unit import (
    ContentUnit
)

from app.vectorstore.qdrant_service import (
    qdrant_service,
    CONTENT_COLLECTION
)


def content_unit_to_payload(
    unit: ContentUnit
) -> dict:

    return {
        "unit_id": unit.unit_id,

        "source_id": unit.source_id,
        "source_type": unit.source_type,

        "location": unit.location,

        "content_type": unit.content_type,

        "text": unit.text,

        "visual_description":
            unit.visual_description,

        "image_path":
            unit.image_path,

        "topic":
            unit.topic,

        "subtopic":
            unit.subtopic,

        "concept_ids":
            unit.concept_ids
    }


def store_content_units(
    units: list[ContentUnit]
):

    points = []


    for unit in units:

        if not unit.embedding:
            continue


        point = PointStruct(
            id=str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                unit.unit_id
            )),

            vector=unit.embedding,

            payload=content_unit_to_payload(
                unit
            )
        )

        points.append(point)


    if not points:

        print(
            "[Qdrant] No embedded units to store."
        )

        return


    print(
        f"[Qdrant] Storing "
        f"{len(points)} content units..."
    )


    qdrant_service.client.upsert(
        collection_name=CONTENT_COLLECTION,
        points=points
    )


    print(
        "[Qdrant] Content units stored."
    )