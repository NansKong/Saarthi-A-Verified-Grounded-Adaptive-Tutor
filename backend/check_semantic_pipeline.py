from app.schemas.content_unit import (
    ContentUnit
)

from app.processing.semantic_processor import (
    enrich_content_units
)

from app.knowledge.concept_registry import (
    ConceptRegistry
)


registry = ConceptRegistry()


units = [

    ContentUnit(
        unit_id="pdf_unit_1",
        source_id="ml_book.pdf",
        source_type="pdf",

        location={
            "page": 10
        },

        chunk_index=1,
        content_type="text",

        text=(
            "Gradient descent minimizes a loss "
            "function by updating parameters "
            "opposite to the gradient."
        ),

        visual_description=None,
        image_path=None,

        topic=None,
        subtopic=None,
        concept_ids=[]
    ),


    ContentUnit(
        unit_id="ppt_unit_1",
        source_id="optimization.pptx",
        source_type="slides",

        location={
            "slide": 6
        },

        chunk_index=1,
        content_type="text",

        text=(
            "The learning rate determines the "
            "size of parameter updates during "
            "gradient descent optimization."
        ),

        visual_description=None,
        image_path=None,

        topic=None,
        subtopic=None,
        concept_ids=[]
    ),


    ContentUnit(
        unit_id="video_unit_1",
        source_id="lecture.mp4",
        source_type="video",

        location={
            "timestamp": {
                "start": 120,
                "end": 165
            }
        },

        chunk_index=1,
        content_type="text",

        text=(
            "The gradient descent algorithm "
            "iteratively changes model parameters "
            "to reduce the cost function."
        ),

        visual_description=None,
        image_path=None,

        topic=None,
        subtopic=None,
        concept_ids=[]
    )

]


units = enrich_content_units(
    units=units,
    registry=registry
)


print("\nENRICHED CONTENT UNITS")
print("=" * 70)


for unit in units:

    print()

    print("Unit:", unit.unit_id)
    print("Source:", unit.source_type)

    print(
        "Location:",
        unit.location
    )

    print(
        "Topic:",
        unit.topic
    )

    print(
        "Subtopic:",
        unit.subtopic
    )

    print(
        "Concept IDs:",
        unit.concept_ids
    )


print("\nCANONICAL CONCEPT REGISTRY")
print("=" * 70)


for concept in registry.get_all_concepts():

    print()

    print(
        "ID:",
        concept.concept_id
    )

    print(
        "Name:",
        concept.name
    )

    print(
        "Aliases:",
        concept.aliases
    )

    print(
        "Evidence:",
        concept.evidence_units
    )