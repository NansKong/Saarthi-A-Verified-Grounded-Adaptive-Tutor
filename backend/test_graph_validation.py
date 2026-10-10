from app.knowledge.concept_registry import (
    ConceptRegistry
)


registry = ConceptRegistry()


registry.add_concept(
    concept_id="gradient",
    name="Gradient"
)

registry.add_concept(
    concept_id="gradient_descent",
    name="Gradient Descent"
)

registry.add_concept(
    concept_id="backpropagation",
    name="Backpropagation"
)


print("\nAdding valid relationships")
print("=" * 60)


result1 = registry.add_prerequisite(
    concept_id="gradient_descent",
    prerequisite_id="gradient"
)

print(
    "Gradient -> Gradient Descent:",
    result1
)


result2 = registry.add_prerequisite(
    concept_id="backpropagation",
    prerequisite_id="gradient_descent"
)

print(
    "Gradient Descent -> Backpropagation:",
    result2
)


print("\nAttempting invalid cycle")
print("=" * 60)


result3 = registry.add_prerequisite(
    concept_id="gradient",
    prerequisite_id="backpropagation"
)

print(
    "Backpropagation -> Gradient:",
    result3
)


print("\nFINAL GRAPH")
print("=" * 60)


for concept in registry.get_all_concepts():

    print(
        concept.name,
        "requires",
        concept.prerequisites
    )