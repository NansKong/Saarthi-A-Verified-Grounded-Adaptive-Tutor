from app.schemas.content_unit import (
    ContentUnit
)

from app.processing.embedding_processor import (
    embed_content_units
)

from app.vectorstore.content_store import (
    store_content_units
)

from app.vectorstore.qdrant_service import (
    qdrant_service,
    CONTENT_COLLECTION
)


units = [

    ContentUnit(
        unit_id="pdf_gradient_1",

        source_id="machine_learning.pdf",

        source_type="pdf",

        location={
            "page": 14
        },

        chunk_index=1,

        content_type="text",

        text=(
            "Gradient descent minimizes a loss "
            "function by moving parameters opposite "
            "to the gradient."
        ),

        topic="Machine Learning",

        subtopic="Optimization",

        concept_ids=[
            "gradient_descent",
            "gradient",
            "loss_function"
        ]
    ),


    ContentUnit(
        unit_id="ppt_neural_1",

        source_id="neural_networks.pptx",

        source_type="slides",

        location={
            "slide": 8
        },

        chunk_index=1,

        content_type="text",

        text=(
            "Backpropagation computes gradients "
            "through layers of a neural network."
        ),

        topic="Machine Learning",

        subtopic="Neural Networks",

        concept_ids=[
            "backpropagation",
            "gradient",
            "neural_network"
        ]
    )
]


units = embed_content_units(
    units
)


store_content_units(
    units
)


info = (
    qdrant_service.client
    .get_collection(
        CONTENT_COLLECTION
    )
)


print("\nQDRANT COLLECTION")
print("=" * 60)

print(
    "Points:",
    info.points_count
)

qdrant_service.close()