from app.vectorstore.content_search import (
    search_content
)

from app.vectorstore.qdrant_service import (
    qdrant_service
)


query = (
    "How does gradient descent reduce the loss?"
)


results = search_content(
    query=query,
    limit=5
)


print("\nQUERY")
print("=" * 70)

print(query)


print("\nSEARCH RESULTS")
print("=" * 70)


for index, result in enumerate(
    results,
    start=1
):

    print()
    print(
        f"Result {index}"
    )

    print(
        f"Score: "
        f"{result['score']:.4f}"
    )

    print(
        "Source:",
        result["source_id"]
    )

    print(
        "Type:",
        result["source_type"]
    )

    print(
        "Location:",
        result["location"]
    )

    print(
        "Topic:",
        result["topic"]
    )

    print(
        "Subtopic:",
        result["subtopic"]
    )

    print(
        "Concepts:",
        result["concept_ids"]
    )

    print(
        "Text:",
        result["text"]
    )


qdrant_service.close()