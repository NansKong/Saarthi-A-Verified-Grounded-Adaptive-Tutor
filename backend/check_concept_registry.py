from app.schemas.content_unit import ContentUnit

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.concept_registry_processor import (
    process_unit_concepts
)


registry = ConceptRegistry()


unit1 = ContentUnit(
    unit_id="unit_001",
    source_id="machine_learning.pdf",
    source_type="pdf",
    location={"page": 10},
    chunk_index=1,
    content_type="text",

    text=(
        "Gradient descent is an optimization algorithm "
        "used to minimize a loss function."
    ),

    visual_description=None,
    image_path=None,

    topic=None,
    subtopic=None,
    concept_ids=[]
)


unit2 = ContentUnit(
    unit_id="unit_002",
    source_id="lecture_1.mp4",
    source_type="video",

    location={
        "timestamp": {
            "start": 120,
            "end": 165
        }
    },

    chunk_index=2,
    content_type="text",

    text=(
        "The gradient descent algorithm repeatedly updates "
        "parameters to reduce the cost function."
    ),

    visual_description=None,
    image_path=None,

    topic=None,
    subtopic=None,
    concept_ids=[]
)


process_unit_concepts(
    unit1,
    registry
)

process_unit_concepts(
    unit2,
    registry
)


print("\nUNIT 1")
print("=" * 60)

print("Topic:", unit1.topic)
print("Subtopic:", unit1.subtopic)
print("Concept IDs:", unit1.concept_ids)


print("\nUNIT 2")
print("=" * 60)

print("Topic:", unit2.topic)
print("Subtopic:", unit2.subtopic)
print("Concept IDs:", unit2.concept_ids)


print("\nCANONICAL CONCEPT REGISTRY")
print("=" * 60)


for concept in registry.get_all_concepts():

    print()
    print("ID:", concept.concept_id)
    print("Name:", concept.name)
    print("Aliases:", concept.aliases)
    print("Topic:", concept.topic)
    print("Subtopic:", concept.subtopic)
    print("Evidence:", concept.evidence_units)