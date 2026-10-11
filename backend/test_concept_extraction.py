from app.schemas.content_unit import ContentUnit
from app.processing.concept_extractor import (
    extract_semantic_metadata
)


unit = ContentUnit(
    unit_id="test_001",

    source_id="machine_learning.pdf",

    source_type="pdf",

    location={
        "page": 14
    },

    chunk_index=1,

    content_type="text",

    text=(
        "Gradient descent is an optimization algorithm used "
        "to minimize a loss function. Model parameters are "
        "updated iteratively in the direction opposite to "
        "the gradient. The learning rate controls the size "
        "of each parameter update."
    ),

    visual_description=None,

    image_path=None,

    topic=None,
    subtopic=None,

    concept_ids=[]
)


result = extract_semantic_metadata(unit)


print("\nSemantic Metadata")
print("=" * 60)

print(f"Topic: {result['topic']}")
print(f"Subtopic: {result['subtopic']}")

print("\nConcepts:")

for concept in result["concepts"]:
    print(f"- {concept}")

print("\nConcept IDs:")

for concept_id in result["concept_ids"]:
    print(f"- {concept_id}")