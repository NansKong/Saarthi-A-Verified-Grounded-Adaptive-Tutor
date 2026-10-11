from app.knowledge.concept_registry import ConceptRegistry

from app.knowledge.graph_queries import (
    get_direct_prerequisites,
    get_all_prerequisites,
    get_learning_order,
    get_direct_dependents,
    get_all_dependents
)


registry = ConceptRegistry()


# -------------------------------------------------
# Concepts
# -------------------------------------------------

registry.add_concept(
    concept_id="derivative",
    name="Derivative"
)

registry.add_concept(
    concept_id="gradient",
    name="Gradient"
)

registry.add_concept(
    concept_id="loss_function",
    name="Loss Function"
)

registry.add_concept(
    concept_id="gradient_descent",
    name="Gradient Descent"
)

registry.add_concept(
    concept_id="neural_network",
    name="Neural Network"
)

registry.add_concept(
    concept_id="backpropagation",
    name="Backpropagation"
)


# -------------------------------------------------
# Prerequisite relationships
# -------------------------------------------------

registry.add_prerequisite(
    concept_id="gradient",
    prerequisite_id="derivative"
)

registry.add_prerequisite(
    concept_id="gradient_descent",
    prerequisite_id="gradient"
)

registry.add_prerequisite(
    concept_id="gradient_descent",
    prerequisite_id="loss_function"
)

registry.add_prerequisite(
    concept_id="backpropagation",
    prerequisite_id="gradient_descent"
)

registry.add_prerequisite(
    concept_id="backpropagation",
    prerequisite_id="neural_network"
)


target = "backpropagation"


# -------------------------------------------------
# Direct prerequisites
# -------------------------------------------------

print("\nDIRECT PREREQUISITES")
print("=" * 70)

direct = get_direct_prerequisites(
    target,
    registry
)

for concept_id in direct:

    concept = registry.get_concept(
        concept_id
    )

    print(
        f"- {concept.name}"
    )


# -------------------------------------------------
# All prerequisites
# -------------------------------------------------

print("\nALL PREREQUISITES")
print("=" * 70)

all_prerequisites = get_all_prerequisites(
    target,
    registry
)

for concept_id in all_prerequisites:

    concept = registry.get_concept(
        concept_id
    )

    print(
        f"- {concept.name}"
    )


# -------------------------------------------------
# Learning order
# -------------------------------------------------

print("\nLEARNING ORDER")
print("=" * 70)

learning_order = get_learning_order(
    target,
    registry
)

for index, concept_id in enumerate(
    learning_order,
    start=1
):

    concept = registry.get_concept(
        concept_id
    )

    print(
        f"{index}. {concept.name}"
    )


# -------------------------------------------------
# Dependents
# -------------------------------------------------

print("\nDIRECT DEPENDENTS OF DERIVATIVE")
print("=" * 70)

dependents = get_direct_dependents(
    "derivative",
    registry
)

for concept_id in dependents:

    concept = registry.get_concept(
        concept_id
    )

    print(
        f"- {concept.name}"
    )


print("\nALL DEPENDENTS OF DERIVATIVE")
print("=" * 70)

all_dependents = get_all_dependents(
    "derivative",
    registry
)

for concept_id in all_dependents:

    concept = registry.get_concept(
        concept_id
    )

    print(
        f"- {concept.name}"
    )