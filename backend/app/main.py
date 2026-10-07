from fastapi import FastAPI

from app.api.knowledge import router as knowledge_router


app = FastAPI(
    title="Saarthi Knowledge Base API",
    version="0.1.0"
)


app.include_router(knowledge_router)


@app.get("/")
def root():
    return {
        "message": "Saarthi Multimodal Knowledge Base API is running."
    }