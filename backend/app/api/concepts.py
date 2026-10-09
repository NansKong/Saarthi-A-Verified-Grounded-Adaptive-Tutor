from fastapi import APIRouter

from app.knowledge.course_registry import (
    course_concept_registry
)


router = APIRouter(
    prefix="/concepts",
    tags=["Concepts"]
)


@router.get("/")
def get_concepts():

    concepts = (
        course_concept_registry.to_dict()
    )

    return {
        "concept_count": len(concepts),
        "concepts": concepts
    }