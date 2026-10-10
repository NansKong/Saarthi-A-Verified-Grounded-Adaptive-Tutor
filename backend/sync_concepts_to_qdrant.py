from app.knowledge.course_registry import (
    course_concept_registry
)

from app.vectorstore.concept_store import (
    store_concepts
)

from app.vectorstore.qdrant_service import (
    qdrant_service
)


print("\nSYNCING EXISTING CONCEPT REGISTRY")
print("=" * 70)

store_concepts(
    course_concept_registry
)

print("\nConcept registry synced to Qdrant.")

qdrant_service.close()