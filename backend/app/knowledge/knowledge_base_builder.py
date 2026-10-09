from pathlib import Path

from groq import RateLimitError

from app.ingestion.pdf_pipeline import (
    process_pdf
)

from app.ingestion.ppt_pipeline import (
    process_ppt
)

from app.ingestion.video_pipeline import (
    process_video
)

from app.knowledge.course_registry import (
    course_concept_registry
)

from app.processing.knowledge_graph_builder import (
    build_knowledge_graph
)

from app.knowledge.graph_validator import (
    validate_graph
)

from app.vectorstore.content_store import (
    store_content_units
)

from app.vectorstore.concept_store import (
    store_concepts
)

from app.llm.text_llm import (
    LLMUnavailableError
)


# =====================================================
# Pipeline result helper
# =====================================================

def _extract_content_units(
    pipeline_result
):
    """
    Normalize the output returned by PDF/PPT/video
    pipelines into a plain list of ContentUnit objects.

    Supports:
    - direct list
    - dictionary
    - tuple
    """

    # -------------------------------------------------
    # Direct list
    # -------------------------------------------------

    if isinstance(
        pipeline_result,
        list
    ):

        return pipeline_result


    # -------------------------------------------------
    # Dictionary result
    # -------------------------------------------------

    if isinstance(
        pipeline_result,
        dict
    ):

        possible_keys = [
            "all_units",
            "content_units",
            "units"
        ]


        for key in possible_keys:

            value = pipeline_result.get(
                key
            )


            if isinstance(
                value,
                list
            ):

                return value


        raise ValueError(
            "Pipeline returned a dictionary, "
            "but no ContentUnit list was found. "
            f"Available keys: "
            f"{list(pipeline_result.keys())}"
        )


    # -------------------------------------------------
    # Tuple result
    #
    # Some ingestion pipelines may return:
    #
    # (all_units, text_units, visual_units)
    # -------------------------------------------------

    if isinstance(
        pipeline_result,
        tuple
    ):

        for value in pipeline_result:

            if isinstance(
                value,
                list
            ):

                # Prefer the largest list because
                # all_units normally contains both
                # text and visual units.
                pass


        lists = [
            value
            for value in pipeline_result
            if isinstance(
                value,
                list
            )
        ]


        if lists:

            return max(
                lists,
                key=len
            )


    raise TypeError(
        "Unsupported ingestion pipeline result: "
        f"{type(pipeline_result).__name__}"
    )


# =====================================================
# Main knowledge-base builder
# =====================================================

def build_knowledge_base(
    file_path: str
) -> dict:

    path = Path(
        file_path
    )

    filename = path.name

    extension = (
        path.suffix
        .lower()
    )


    print()

    print(
        "=" * 70
    )

    print(
        f"[Knowledge Base] "
        f"Processing: {filename}"
    )

    print(
        "=" * 70
    )


    # =================================================
    # 1. INGEST SOURCE
    # =================================================

    if extension == ".pdf":

        print(
            "[Knowledge Base] "
            "Source type: PDF"
        )


        pipeline_result = process_pdf(
            str(path)
        )


        source_type = "pdf"


    elif extension == ".pptx":

        print(
            "[Knowledge Base] "
            "Source type: PPTX"
        )


        pipeline_result = process_ppt(
            str(path)
        )


        source_type = "slides"


    elif extension == ".mp4":

        print(
            "[Knowledge Base] "
            "Source type: VIDEO"
        )


        pipeline_result = process_video(
            str(path)
        )


        source_type = "video"


    else:

        raise ValueError(
            f"Unsupported file type: "
            f"{extension}"
        )


    # =================================================
    # 2. NORMALIZE PIPELINE RESULT
    # =================================================

    all_units = _extract_content_units(
        pipeline_result
    )


    print(
        f"[Knowledge Base] "
        f"{len(all_units)} "
        f"ContentUnits produced."
    )


    # =================================================
    # 3. FIND AFFECTED CONCEPTS
    # =================================================

    affected_concept_ids = set()


    for unit in all_units:

        concept_ids = getattr(
            unit,
            "concept_ids",
            []
        )


        if concept_ids:

            affected_concept_ids.update(
                concept_ids
            )


    print(
        f"[Knowledge Base] "
        f"Concepts affected by current upload: "
        f"{len(affected_concept_ids)}"
    )


    # =================================================
    # 4. STORE CONTENT UNITS
    # =================================================

    print(
        "[Knowledge Base] "
        "Storing ContentUnits in Qdrant..."
    )


    store_content_units(
        all_units
    )


    # =================================================
    # 5. SYNC CONCEPTS BEFORE GRAPH
    # =================================================

    print(
        "[Knowledge Base] "
        "Syncing concept registry..."
    )


    store_concepts(
        course_concept_registry
    )


    # =================================================
    # 6. BUILD PREREQUISITE GRAPH
    # =================================================

    graph_status = "completed"

    graph_error = None


    if not affected_concept_ids:

        print(
            "[Knowledge Base] "
            "No concepts found for "
            "prerequisite graph generation."
        )


        validation = validate_graph(
            course_concept_registry
        )


        graph_status = (
            "skipped_no_concepts"
        )


        graph_error = (
            "No concepts were extracted "
            "from the current upload."
        )


    else:

        print(
            "[Knowledge Base] "
            "Building prerequisite graph..."
        )


        try:

            build_knowledge_graph(
                registry=course_concept_registry,
                concept_ids=affected_concept_ids
            )


            validation = validate_graph(
                course_concept_registry
            )


            graph_status = "completed"

            graph_error = None


        # ---------------------------------------------
        # Compatibility with any old Groq-only paths
        # ---------------------------------------------

        except RateLimitError:

            print(
                "[Knowledge Base] "
                "Groq rate limit reached."
            )


            print(
                "[Knowledge Base] "
                "Prerequisite graph generation deferred."
            )


            print(
                "[Knowledge Base] "
                "Completed checkpoints are preserved."
            )


            validation = validate_graph(
                course_concept_registry
            )


            graph_status = (
                "deferred_rate_limit"
            )


            graph_error = (
                "LLM rate limit reached. "
                "Completed checkpoints were preserved "
                "and processing can resume later."
            )


        # ---------------------------------------------
        # Groq + Gemini unavailable
        # ---------------------------------------------

        except LLMUnavailableError:

            print(
                "[Knowledge Base] "
                "All LLM providers are "
                "temporarily unavailable."
            )


            print(
                "[Knowledge Base] "
                "Prerequisite graph generation deferred."
            )


            print(
                "[Knowledge Base] "
                "Completed checkpoints are preserved."
            )


            validation = validate_graph(
                course_concept_registry
            )


            graph_status = (
                "deferred_llm_unavailable"
            )


            graph_error = (
                "All configured LLM providers were "
                "temporarily unavailable. "
                "Completed checkpoints were preserved "
                "and processing can safely resume later."
            )


    # =================================================
    # 7. SAVE PARTIAL / COMPLETE GRAPH
    # =================================================

    print(
        "[Knowledge Base] "
        "Updating concept graph in Qdrant..."
    )


    store_concepts(
        course_concept_registry
    )


    # =================================================
    # 8. CONCEPT RESPONSE
    # =================================================

    concepts_response = []


    concepts = (
        course_concept_registry
        .get_all_concepts()
    )


    for concept in concepts:

        concepts_response.append(
            {
                "concept_id":
                    concept.concept_id,

                "name":
                    concept.name,

                "aliases":
                    list(
                        concept.aliases
                    ),

                "topic":
                    concept.topic,

                "subtopic":
                    concept.subtopic,

                "evidence_units":
                    list(
                        concept.evidence_units
                    ),

                "prerequisites":
                    list(
                        concept.prerequisites
                    )
            }
        )


    # =================================================
    # 9. GRAPH COUNTS
    # =================================================

    concept_count = len(
        concepts
    )


    edge_count = sum(
        len(
            concept.prerequisites
        )
        for concept in concepts
    )


    # =================================================
    # 10. RETURN
    # =================================================

    return {
        "filename":
            filename,

        "source_type":
            source_type,

        "content_unit_count":
            len(all_units),

        "affected_concept_count":
            len(affected_concept_ids),

        "concept_count":
            concept_count,

        "edge_count":
            edge_count,

        "has_cycles":
            validation.get(
                "has_cycles",
                False
            ),

        "cycle_nodes":
            validation.get(
                "cycle_nodes",
                []
            ),

        "graph_status":
            graph_status,

        "graph_error":
            graph_error,

        "content_units":
            all_units,

        "concepts":
            concepts_response
    }