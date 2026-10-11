from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.vectorstore.concept_store import (
    store_concepts
)

from app.vectorstore.concept_search import (
    search_similar_concepts
)

from app.processing.concept_normalizer import (
    resolve_concept
)

from app.vectorstore.qdrant_service import (
    qdrant_service
)


registry = ConceptRegistry()


registry.add_concept(
    concept_id="gradient_descent",
    name="Gradient Descent",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="gradient",
    name="Gradient",
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
    concept_id="loss_function",
    name="Loss Function",
    topic="Machine Learning",
    subtopic="Optimization"
)


registry.add_concept(
    concept_id="linear_regression",
    name="Linear Regression",
    topic="Machine Learning",
    subtopic="Regression"
)


print("\nSYNCING CONCEPT REGISTRY")
print("=" * 70)


store_concepts(
    registry
)


query_concept = "Stochastic Gradient Descent"
print("\nVECTOR CANDIDATES")
print("=" * 70)


candidates = (
    search_similar_concepts(
        concept_name=query_concept,

        topic="Machine Learning",

        subtopic="Optimization",

        limit=5
    )
)


for candidate in candidates:

    print(
        f"{candidate['score']:.4f}"
        f" -> "
        f"{candidate['name']}"
    )


print("\nNORMALIZATION RESULT")
print("=" * 70)


result = resolve_concept(
    concept_name=query_concept,

    topic="Machine Learning",

    subtopic="Optimization",

    registry=registry,

    top_k=5
)


print(
    result
)


qdrant_service.close()