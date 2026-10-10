from app.schemas.content_unit import ContentUnit

from app.processing.semantic_processor import (
    enrich_content_units
)

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.knowledge_graph_builder import (
    build_knowledge_graph
)


registry = ConceptRegistry()


units = [

    ContentUnit(
        unit_id="pdf_unit_1",
        source_id="ml_book.pdf",
        source_type="pdf",
        location={"page": 10},
        chunk_index=1,
        content_type="text",

        text=(
            "Gradient descent minimizes a loss function "
            "by moving model parameters opposite to the gradient."
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
        location={"slide": 6},
        chunk_index=1,
        content_type="text",

        text=(
            "The learning rate controls the size of "
            "parameter updates during gradient descent."
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
            "Backpropagation computes gradients through "
            "a neural network and uses them to update model parameters."
        ),

        visual_description=None,
        image_path=None,

        topic=None,
        subtopic=None,
        concept_ids=[]
    )
]


print("\nSTEP 1: Semantic enrichment")
print("=" * 70)

units = enrich_content_units(
    units=units,
    registry=registry
)


print("\nSTEP 2: Concepts discovered")
print("=" * 70)

for concept in registry.get_all_concepts():

    print(
        concept.concept_id,
        "->",
        concept.name
    )


print("\nSTEP 3: Build knowledge graph")
print("=" * 70)

result = build_knowledge_graph(
    registry
)


registry = result["registry"]
validation = result["validation"]


print("\nPREREQUISITE GRAPH")
print("=" * 70)

for concept in registry.get_all_concepts():

    if not concept.prerequisites:
        print(
            f"{concept.name}: no prerequisites"
        )

    else:

        prerequisite_names = []

        for prerequisite_id in concept.prerequisites:

            prerequisite = registry.get_concept(
                prerequisite_id
            )

            if prerequisite:
                prerequisite_names.append(
                    prerequisite.name
                )

        print(
            f"{concept.name}: "
            f"{prerequisite_names}"
        )


print("\nGRAPH EDGES")
print("=" * 70)

for concept in registry.get_all_concepts():

    for prerequisite_id in concept.prerequisites:

        prerequisite = registry.get_concept(
            prerequisite_id
        )

        if prerequisite:

            print(
                f"{prerequisite.name} "
                f"--> "
                f"{concept.name}"
            )


print("\nGRAPH VALIDATION")
print("=" * 70)

print(
    "Concept count:",
    validation["concept_count"]
)

print(
    "Edge count:",
    validation["edge_count"]
)

print(
    "Has cycles:",
    validation["has_cycles"]
)

print(
    "Cycle nodes:",
    validation["cycle_nodes"]
) 