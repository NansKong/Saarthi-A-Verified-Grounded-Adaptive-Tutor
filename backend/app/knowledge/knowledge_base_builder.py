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
    Normalize PDF/PPT/video pipeline output into
    a plain ContentUnit list.

    Supported:
    - list
    - dictionary
    - tuple
    """

    # =================================================
    # Direct list
    # =================================================

    if isinstance(
        pipeline_result,
        list
    ):

        return pipeline_result


    # =================================================
    # Dictionary
    # =================================================

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

            value = (
                pipeline_result.get(
                    key
                )
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


    # =================================================
    # Tuple
    # =================================================

    if isinstance(
        pipeline_result,
        tuple
    ):

        lists = [
            value
            for value in pipeline_result
            if isinstance(
                value,
                list
            )
        ]


        if lists:

            # all_units normally contains the
            # largest number of entries.
            return max(
                lists,
                key=len
            )


    raise TypeError(
        "Unsupported ingestion pipeline result: "
        f"{type(pipeline_result).__name__}"
    )


# =====================================================
# Semantic pipeline status helper
# =====================================================

def _extract_semantic_status(
    pipeline_result
) -> tuple[str, str | None]:

    if not isinstance(
        pipeline_result,
        dict
    ):

        return (
            "completed",
            None
        )


    semantic_status = (
        pipeline_result.get(
            "semantic_status",
            "completed"
        )
    )


    semantic_error = (
        pipeline_result.get(
            "semantic_error"
        )
    )


    return (
        semantic_status,
        semantic_error
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


    filename = (
        path.name
    )


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
        f"Processing: "
        f"{filename}"
    )

    print(
        "=" * 70
    )


    # =====================================================
    # 1. INGEST SOURCE
    # =====================================================

    if extension == ".pdf":

        print(
            "[Knowledge Base] "
            "Source type: PDF"
        )


        pipeline_result = (
            process_pdf(
                str(
                    path
                )
            )
        )


        source_type = "pdf"


    elif extension == ".pptx":

        print(
            "[Knowledge Base] "
            "Source type: PPTX"
        )


        pipeline_result = (
            process_ppt(
                str(
                    path
                )
            )
        )


        source_type = "slides"


    elif extension == ".mp4":

        print(
            "[Knowledge Base] "
            "Source type: VIDEO"
        )


        pipeline_result = (
            process_video(
                str(
                    path
                )
            )
        )


        source_type = "video"


    else:

        raise ValueError(
            f"Unsupported file type: "
            f"{extension}"
        )


    # =====================================================
    # 2. NORMALIZE PIPELINE RESULT
    # =====================================================

    all_units = (
        _extract_content_units(
            pipeline_result
        )
    )


    semantic_status, semantic_error = (
        _extract_semantic_status(
            pipeline_result
        )
    )


    print(
        f"[Knowledge Base] "
        f"{len(all_units)} "
        f"ContentUnits produced."
    )


    print(
        "[Knowledge Base] "
        f"Semantic status: "
        f"{semantic_status}"
    )


    # =====================================================
    # 3. FIND AFFECTED CONCEPTS
    # =====================================================

    affected_concept_ids = (
        set()
    )


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
        f"Concepts affected by "
        f"current upload: "
        f"{len(affected_concept_ids)}"
    )


    # =====================================================
    # 4. STORE CONTENT UNITS
    #
    # This now happens even if semantic enrichment was
    # partially deferred by the video pipeline.
    # =====================================================

    print(
        "[Knowledge Base] "
        "Storing ContentUnits in Qdrant..."
    )


    store_content_units(
        all_units
    )


    # =====================================================
    # 5. SYNC CONCEPTS BEFORE GRAPH
    # =====================================================

    print(
        "[Knowledge Base] "
        "Syncing concept registry..."
    )


    store_concepts(
        course_concept_registry
    )


    # =====================================================
    # 6. BUILD PREREQUISITE GRAPH
    # =====================================================

    graph_status = (
        "completed"
    )

    graph_error = None


    # -----------------------------------------------------
    # If semantic enrichment itself is deferred,
    # don't try generating a graph from an incomplete
    # concept set.
    # -----------------------------------------------------

    if semantic_status != "completed":

        print(
            "[Knowledge Base] "
            "Semantic processing is incomplete."
        )

        print(
            "[Knowledge Base] "
            "Prerequisite graph generation deferred."
        )


        validation = validate_graph(
            course_concept_registry
        )


        graph_status = (
            "deferred_semantic_processing"
        )


        graph_error = (
            "Prerequisite graph generation was "
            "deferred because semantic enrichment "
            "did not fully complete."
        )


    elif not affected_concept_ids:

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
                registry=(
                    course_concept_registry
                ),

                concept_ids=(
                    affected_concept_ids
                )
            )


            validation = validate_graph(
                course_concept_registry
            )


            graph_status = (
                "completed"
            )

            graph_error = None


        # =================================================
        # Compatibility with old direct Groq paths
        # =================================================

        except RateLimitError:

            print(
                "[Knowledge Base] "
                "Groq rate limit reached."
            )


            print(
                "[Knowledge Base] "
                "Prerequisite graph generation "
                "deferred."
            )


            print(
                "[Knowledge Base] "
                "Completed checkpoints are "
                "preserved."
            )


            validation = validate_graph(
                course_concept_registry
            )


            graph_status = (
                "deferred_rate_limit"
            )


            graph_error = (
                "LLM rate limit reached. "
                "Completed checkpoints were "
                "preserved and processing "
                "can resume later."
            )


        # =================================================
        # Groq + Gemini unavailable
        # =================================================

        except LLMUnavailableError as exc:

            print(
                "[Knowledge Base] "
                "All LLM providers are "
                "temporarily unavailable."
            )


            print(
                "[Knowledge Base] "
                "Prerequisite graph generation "
                "deferred."
            )


            print(
                "[Knowledge Base] "
                "Completed checkpoints are "
                "preserved."
            )


            validation = validate_graph(
                course_concept_registry
            )


            graph_status = (
                "deferred_llm_unavailable"
            )


            graph_error = str(
                exc
            )


    # =====================================================
    # 7. SAVE PARTIAL / COMPLETE GRAPH
    # =====================================================

    print(
        "[Knowledge Base] "
        "Updating concept graph in Qdrant..."
    )


    store_concepts(
        course_concept_registry
    )


    # =====================================================
    # 8. CONCEPT RESPONSE
    # =====================================================

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


    # =====================================================
    # 9. GRAPH COUNTS
    # =====================================================

    concept_count = len(
        concepts
    )


    edge_count = sum(
        len(
            concept.prerequisites
        )
        for concept in concepts
    )


    # =====================================================
    # 10. RETURN
    # =====================================================

    return {
        "filename":
            filename,

        "source_type":
            source_type,

        "content_unit_count":
            len(
                all_units
            ),

        "affected_concept_count":
            len(
                affected_concept_ids
            ),

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

        # ---------------------------------------------
        # Semantic stage
        # ---------------------------------------------

        "semantic_status":
            semantic_status,

        "semantic_error":
            semantic_error,

        # ---------------------------------------------
        # Graph stage
        # ---------------------------------------------

        "graph_status":
            graph_status,

        "graph_error":
            graph_error,

        # ---------------------------------------------
        # Data
        # ---------------------------------------------

        "content_units":
            all_units,

        "concepts":
            concepts_response
    }