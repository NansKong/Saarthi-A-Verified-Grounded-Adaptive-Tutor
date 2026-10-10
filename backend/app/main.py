from fastapi import FastAPI

from app.api.knowledge import router as knowledge_router
from app.api.concepts import (
    router as concepts_router
)

from app.api.graph import (
    router as graph_router
)

from app.api.search import (
    router as search_router
)

app = FastAPI(
    title="Saarthi Knowledge Base API",
    version="0.1.0"
)


app.include_router(knowledge_router)
app.include_router(concepts_router)
app.include_router(
    graph_router
)

app.include_router(
    search_router
)

@app.get("/")
def root():
    return {
        "message": "Saarthi Multimodal Knowledge Base API is running."
    }