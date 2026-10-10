from fastapi import (
    APIRouter,
    Query
)

from app.vectorstore.content_search import (
    search_content
)


router = APIRouter(
    prefix="/search",
    tags=["Semantic Search"]
)


@router.get("/")
def semantic_search(
    q: str = Query(
        ...,
        min_length=2
    ),

    limit: int = Query(
        5,
        ge=1,
        le=20
    )
):

    results = search_content(
        query=q,
        limit=limit
    )


    return {
        "query":
            q,

        "result_count":
            len(results),

        "results":
            results
    }