from app.schemas.content_unit import (
    ContentUnit
)

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.concept_extractor import (
    extract_semantic_metadata
)

from app.processing.batch_concept_normalizer import (
    resolve_concepts_batch
)

from app.vectorstore.concept_store import (
    store_concept
)


def apply_semantic_metadata_batch(
    units: list[ContentUnit],
    metadata_by_unit: dict,
    registry: ConceptRegistry
) -> list[ContentUnit]:

    normalization_requests = []

    request_mapping = {}


    # =====================================================
    # Prepare every concept in the semantic batch
    # =====================================================

    for unit in units:

        metadata = (
            metadata_by_unit.get(
                unit.unit_id
            )
        )


        if metadata is None:
            continue


        topic = metadata.get(
            "topic"
        )

        subtopic = metadata.get(
            "subtopic"
        )


        unit.topic = topic
        unit.subtopic = subtopic


        concepts = metadata.get(
            "concepts",
            []
        )


        if not isinstance(
            concepts,
            list
        ):

            concepts = []


        for concept_index, concept_name in enumerate(
            concepts
        ):

            if not isinstance(
                concept_name,
                str
            ):
                continue


            concept_name = (
                concept_name.strip()
            )


            if not concept_name:
                continue


            request_id = (
                f"{unit.unit_id}"
                f"::concept_"
                f"{concept_index}"
            )


            normalization_requests.append(
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
            )


            request_mapping[
                request_id
            ] = {
                "unit":
                    unit,

                "concept_name":
                    concept_name
            }


    # =====================================================
    # ONE batch normalization operation
    # =====================================================

    resolved = {}


    if normalization_requests:

        resolved = (
            resolve_concepts_batch(
                requests=normalization_requests,
                registry=registry
            )
        )


    # =====================================================
    # Apply resolved concepts
    # =====================================================

    unit_concept_ids = {
        unit.unit_id: []
        for unit in units
    }


    for request_id, resolution in (
        resolved.items()
    ):

        mapping = (
            request_mapping.get(
                request_id
            )
        )


        if not mapping:
            continue


        unit = mapping[
            "unit"
        ]

        concept_name = mapping[
            "concept_name"
        ]


        concept_id = (
            resolution[
                "concept_id"
            ]
        )

        canonical_name = (
            resolution[
                "canonical_name"
            ]
        )


        aliases = []


        if (
            concept_name.strip().lower()
            !=
            canonical_name.strip().lower()
        ):

            aliases.append(
                concept_name
            )


        record = (
            registry.add_concept(
                concept_id=concept_id,
                name=canonical_name,

                topic=(
                    unit.topic
                    if resolution["is_new"]
                    else None
                ),

                subtopic=(
                    unit.subtopic
                    if resolution["is_new"]
                    else None
                ),

                aliases=aliases,

                evidence_unit=(
                    unit.unit_id
                )
            )
        )


        store_concept(
            record
        )


        unit_concept_ids[
            unit.unit_id
        ].append(
            concept_id
        )


    # =====================================================
    # Assign IDs back to units
    # =====================================================

    for unit in units:

        unit.concept_ids = list(
            dict.fromkeys(
                unit_concept_ids.get(
                    unit.unit_id,
                    []
                )
            )
        )


    return units


def apply_semantic_metadata(
    unit: ContentUnit,
    metadata: dict,
    registry: ConceptRegistry
) -> ContentUnit:

    apply_semantic_metadata_batch(
        units=[
            unit
        ],

        metadata_by_unit={
            unit.unit_id:
                metadata
        },

        registry=registry
    )


    return unit


def process_unit_concepts(
    unit: ContentUnit,
    registry: ConceptRegistry
) -> ContentUnit:

    metadata = (
        extract_semantic_metadata(
            unit
        )
    )


    return apply_semantic_metadata(
        unit=unit,
        metadata=metadata,
        registry=registry
    )