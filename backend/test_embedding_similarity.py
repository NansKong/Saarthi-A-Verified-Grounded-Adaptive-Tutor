import numpy as np

from app.embeddings.embedding_service import (
    embedding_service
)


sentences = [

    "Gradient descent minimizes a loss function.",

    "The optimizer updates parameters to reduce error.",

    "A convolutional neural network detects image features.",

    "The weather is pleasant today."
]


vectors = embedding_service.encode_batch(
    sentences
)


query = (
    "How does gradient descent reduce the model error?"
)


query_vector = embedding_service.encode(
    query
)


def cosine_similarity(
    vector_a,
    vector_b
):

    a = np.array(vector_a)
    b = np.array(vector_b)

    return float(
        np.dot(a, b)
        /
        (
            np.linalg.norm(a)
            *
            np.linalg.norm(b)
        )
    )


scores = []


for sentence, vector in zip(
    sentences,
    vectors
):

    similarity = cosine_similarity(
        query_vector,
        vector
    )

    scores.append(
        (
            similarity,
            sentence
        )
    )


scores.sort(
    reverse=True
)


print("\nQUERY")
print("=" * 70)

print(query)


print("\nSEMANTIC SEARCH RESULTS")
print("=" * 70)


for score, sentence in scores:

    print(
        f"{score:.4f} -> {sentence}"
    )