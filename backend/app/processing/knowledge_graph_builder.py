from app.processing.prerequisite_processor import (
    build_prerequisite_relationships
)

from app.knowledge.graph_validator import (
    validate_graph
)


def build_knowledge_graph(
    registry,
    concept_ids=None
):

    print(
        "[Knowledge Graph] "
        "Building prerequisite relationships..."
    )


    build_prerequisite_relationships(
        registry=registry,
        top_k=8,
        concept_ids=concept_ids
    )


    validation = validate_graph(
        registry
    )


    return {
        "registry": registry,
        "validation": validation
    }