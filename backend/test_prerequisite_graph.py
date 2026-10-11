from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.prerequisite_processor import (
    build_prerequisite_relationships
)


registry = ConceptRegistry()


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
    concept_id="parameter_update",
    name="Parameter Update",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="gradient_descent",
    name="Gradient Descent",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry = build_prerequisite_relationships(
    registry
)


print("\nPREREQUISITE GRAPH")
print("=" * 70)


for concept in registry.get_all_concepts():

    print()
    print(
        f"{concept.name}"
    )

    print(
        "Prerequisites:",
        concept.prerequisites
    )

print("\nGRAPH EDGES")
print("=" * 70)


for concept in registry.get_all_concepts():

    for prerequisite_id in concept.prerequisites:

        prerequisite = registry.get_concept(
            prerequisite_id
        )

        print(
            f"{prerequisite.name} "
            f"--> "
            f"{concept.name}"
        )