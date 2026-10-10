from app.schemas.content_unit import (
    ContentUnit
)

from app.processing.embedding_processor import (
    embed_content_unit,
    build_embedding_text
)


unit = ContentUnit(

    unit_id="test_gradient_descent",

    source_id="machine_learning.pdf",

    source_type="pdf",

    location={
        "page": 14
    },

    chunk_index=1,

    content_type="text",

    text=(
        "Gradient descent minimizes a loss function "
        "by updating parameters in the direction "
        "opposite to the gradient."
    ),

    visual_description=None,
    image_path=None,

    topic="Machine Learning",

    subtopic="Optimization",

    concept_ids=[
        "gradient_descent",
        "gradient",
        "loss_function"
    ]
)


print("\nEMBEDDING TEXT")
print("=" * 70)

print(
    build_embedding_text(unit)
)


unit = embed_content_unit(
    unit
)


print("\nEMBEDDING RESULT")
print("=" * 70)

print(
    "Embedding dimension:",
    len(unit.embedding)
)

print(
    "First 10 values:"
)

print(
    unit.embedding[:10]
)