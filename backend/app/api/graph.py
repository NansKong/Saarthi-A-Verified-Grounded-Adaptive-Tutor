from fastapi import (
    APIRouter,
    HTTPException
)

from app.knowledge.course_registry import (
    course_concept_registry
)

from app.knowledge.graph_queries import (
    get_direct_prerequisites,
    get_all_prerequisites,
    get_learning_path_details,
    get_direct_dependents
)


router = APIRouter(
    prefix="/graph",
    tags=["Knowledge Graph"]
)


@router.get(
    "/concept/{concept_id}"
)
def get_concept_graph(
    concept_id: str
):

    concept = (
        course_concept_registry
        .get_concept(
            concept_id
        )
    )


    if not concept:

        raise HTTPException(
            status_code=404,
            detail="Concept not found."
        )


    return {
        "concept": {
            "concept_id":
                concept.concept_id,

            "name":
                concept.name,

            "topic":
                concept.topic,

            "subtopic":
                concept.subtopic
        },

        "direct_prerequisites":
            get_direct_prerequisites(
                concept_id,
                course_concept_registry
            ),

        "all_prerequisites":
            get_all_prerequisites(
                concept_id,
                course_concept_registry
            ),

        "direct_dependents":
            get_direct_dependents(
                concept_id,
                course_concept_registry
            ),

        "learning_path":
            get_learning_path_details(
                concept_id,
                course_concept_registry
            )
    }