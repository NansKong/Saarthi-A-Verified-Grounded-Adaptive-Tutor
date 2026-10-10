from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:

    def __init__(self):

        print(
            f"[Embeddings] Loading model: "
            f"{MODEL_NAME}"
        )

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        self.dimension = (
            self.model.get_embedding_dimension()
        )

        print(
            f"[Embeddings] Model loaded. "
            f"Dimension: {self.dimension}"
        )


    def encode(
        self,
        text: str
    ) -> list[float]:

        if not text or not text.strip():
            return []

        vector = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return vector.tolist()


    def encode_batch(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=True
        )

        return [
            vector.tolist()
            for vector in vectors
        ]


embedding_service = EmbeddingService()