from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.vectorstore.concept_store import (
    store_concepts
)

from app.vectorstore.concept_search import (
    search_similar_concepts
)

from app.processing.prerequisite_extractor import (
    extract_prerequisites_for_concept
)

from app.processing.prerequisite_processor import (
    build_prerequisite_relationships
)

from app.knowledge.graph_validator import (
    validate_graph
)

from app.vectorstore.qdrant_service import (
    qdrant_service
)


registry = ConceptRegistry()


# ----------------------------------
# Test concept registry
# ----------------------------------

registry.add_concept(
    concept_id="derivative",
    name="Derivative",
    topic="Mathematics",
    subtopic="Calculus"
)


registry.add_concept(
    concept_id="gradient",
    name="Gradient",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="loss_function",
    name="Loss Function",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="learning_rate",
    name="Learning Rate",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="model_parameters",
    name="Model Parameters",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="gradient_descent",
    name="Gradient Descent",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="neural_network",
    name="Neural Network",
    topic="Machine Learning",
    subtopic="Neural Networks"
)


registry.add_concept(
    concept_id="backpropagation",
    name="Backpropagation",
    topic="Machine Learning",
    subtopic="Neural Networks"
)


registry.add_concept(
    concept_id="linear_regression",
    name="Linear Regression",
    topic="Machine Learning",
    subtopic="Regression"
)


registry.add_concept(
    concept_id="logistic_regression",
    name="Logistic Regression",
    topic="Machine Learning",
    subtopic="Classification"
)


# ----------------------------------
# Sync concepts to Qdrant
# ----------------------------------

print("\nSYNCING CONCEPTS")
print("=" * 70)

store_concepts(
    registry
)


# ----------------------------------
# Inspect candidates for one concept
# ----------------------------------

print("\nCANDIDATES FOR GRADIENT DESCENT")
print("=" * 70)


candidates = search_similar_concepts(
    concept_name="Gradient Descent",
    topic="Machine Learning",
    subtopic="Optimization",
    limit=10
)


for candidate in candidates:

    print(
        f"{candidate['score']:.4f}"
        f" -> "
        f"{candidate['name']}"
    )


# ----------------------------------
# Direct prerequisite extraction
# ----------------------------------

print("\nPREREQUISITES FOR GRADIENT DESCENT")
print("=" * 70)


prerequisites = (
    extract_prerequisites_for_concept(
        concept_id="gradient_descent",
        registry=registry,
        top_k=8
    )
)


for prerequisite_id in prerequisites:

    concept = registry.get_concept(
        prerequisite_id
    )

    print(
        f"- {concept.name}"
    )


# ----------------------------------
# Build full graph
# ----------------------------------

print("\nBUILDING FULL GRAPH")
print("=" * 70)


registry = build_prerequisite_relationships(
    registry=registry,
    top_k=8
)


# ----------------------------------
# Print graph edges
# ----------------------------------

print("\nGRAPH EDGES")
print("=" * 70)


for concept in registry.get_all_concepts():

    for prerequisite_id in concept.prerequisites:

        prerequisite = (
            registry.get_concept(
                prerequisite_id
            )
        )

        if prerequisite:

            print(
                f"{prerequisite.name}"
                f" -> "
                f"{concept.name}"
            )


# ----------------------------------
# Validate
# ----------------------------------

validation = validate_graph(
    registry
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


qdrant_service.close()