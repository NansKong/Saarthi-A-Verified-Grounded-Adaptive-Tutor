from contextlib import (
    asynccontextmanager
)

from fastapi import (
    FastAPI
)

from app.api.knowledge import (
    router as knowledge_router
)

from app.api.concepts import (
    router as concepts_router
)

from app.api.graph import (
    router as graph_router
)

from app.api.search import (
    router as search_router
)

from app.knowledge.course_registry import (
    course_concept_registry
)

from app.knowledge.registry_persistence import (
    restore_registry_from_qdrant
)

from app.vectorstore.qdrant_service import (
    qdrant_service
)


# =====================================================
# FastAPI lifespan
# =====================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI
):

    print()
    print(
        "=" * 70
    )

    print(
        "[Saarthi Startup] "
        "Initializing knowledge base..."
    )

    print(
        "=" * 70
    )


    # =================================================
    # Restore persistent concept registry
    # =================================================

    restore_result = (
        restore_registry_from_qdrant(
            course_concept_registry
        )
    )


    app.state.registry_restore = (
        restore_result
    )


    print(
        "[Saarthi Startup] "
        f"Concepts in memory: "
        f"{len(course_concept_registry.get_all_concepts())}"
    )


    print(
        "[Saarthi Startup] "
        "Knowledge base ready."
    )

    print(
        "=" * 70
    )

    print()


    # =================================================
    # Application runs here
    # =================================================

    yield


    # =================================================
    # Shutdown
    # =================================================

    print()
    print(
        "[Saarthi Shutdown] "
        "Closing Qdrant..."
    )


    try:

        qdrant_service.close()


        print(
            "[Saarthi Shutdown] "
            "Qdrant closed."
        )


    except Exception as exc:

        print(
            "[Saarthi Shutdown] "
            f"Qdrant close warning: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )


# =====================================================
# FastAPI app
# =====================================================

app = FastAPI(
    title=(
        "Saarthi Knowledge Base API"
    ),

    version="0.1.0",

    lifespan=lifespan
)


# =====================================================
# Routers
# =====================================================

app.include_router(
    knowledge_router
)

app.include_router(
    concepts_router
)

app.include_router(
    graph_router
)

app.include_router(
    search_router
)


# =====================================================
# Root
# =====================================================

@app.get("/")
def root():

    return {
        "message":
            (
                "Saarthi Multimodal "
                "Knowledge Base API is running."
            ),

        "concepts_loaded":
            len(
                course_concept_registry
                .get_all_concepts()
            )
    }