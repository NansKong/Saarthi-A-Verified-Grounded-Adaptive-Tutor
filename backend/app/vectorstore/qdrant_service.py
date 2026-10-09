from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams
)


QDRANT_PATH = Path("qdrant_data")

CONTENT_COLLECTION = "saarthi_content"
CONCEPT_COLLECTION = "saarthi_concepts"

EMBEDDING_DIMENSION = 384


class QdrantService:

    def __init__(self):

        QDRANT_PATH.mkdir(
            exist_ok=True
        )

        self.client = QdrantClient(
            path=str(QDRANT_PATH)
        )

        self.ensure_collection(
            CONTENT_COLLECTION
        )

        self.ensure_collection(
            CONCEPT_COLLECTION
        )


    def ensure_collection(
        self,
        collection_name: str
    ):

        existing = [
            collection.name
            for collection
            in self.client
            .get_collections()
            .collections
        ]

        if collection_name in existing:

            print(
                f"[Qdrant] Collection exists: "
                f"{collection_name}"
            )

            return


        print(
            f"[Qdrant] Creating collection: "
            f"{collection_name}"
        )


        self.client.create_collection(
            collection_name=collection_name,

            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )


    def close(self):

        self.client.close()


qdrant_service = QdrantService()