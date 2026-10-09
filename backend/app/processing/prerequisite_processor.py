from groq import RateLimitError

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.batch_prerequisite_extractor import (
    extract_prerequisites_for_batch
)

from app.checkpoints.checkpoint_service import (
    load_prerequisite_checkpoint,
    save_prerequisite_checkpoint
)

from app.llm.text_llm import (
    LLMUnavailableError
)


def _restore_checkpoint(
    concept,
    registry: ConceptRegistry
) -> bool:
    """
    Restore one completed prerequisite checkpoint.

    Returns True if a completed checkpoint existed.
    """

    checkpoint = load_prerequisite_checkpoint(
        concept.concept_id
    )


    if not (
        checkpoint
        and checkpoint.get("status")
        == "completed"
    ):

        return False


    prerequisites = checkpoint.get(
        "prerequisites",
        []
    )


    print(
        f"  ↻ Checkpoint found. "
        f"Restoring "
        f"{len(prerequisites)} "
        f"prerequisite(s)."
    )


    for prerequisite_id in prerequisites:

        prerequisite = registry.get_concept(
            prerequisite_id
        )


        if not prerequisite:
            continue


        # ConceptRegistry performs cycle/self checks.
        registry.add_prerequisite(
            concept.concept_id,
            prerequisite_id
        )


    return True


def build_prerequisite_relationships(
    registry: ConceptRegistry,
    concept_ids: set[str] | None = None,
    top_k: int = 8,
    batch_size: int = 6
):
    """
    Build prerequisite relationships using batched
    LLM inference.

    Old architecture:

        1 extraction call per concept
        +
        1 verification call per candidate edge

    New architecture:

        candidate retrieval = local/Qdrant

        6 target concepts
            ↓
        ONE LLM call
            ↓
        confidence validation in Python
            ↓
        cycle validation in ConceptRegistry

    This dramatically reduces API usage.
    """


    all_concepts = list(
        registry.get_all_concepts()
    )


    # =====================================================
    # Restrict graph processing to concepts from
    # current upload
    # =====================================================

    if concept_ids is not None:

        all_concepts = [
            concept
            for concept in all_concepts
            if concept.concept_id
            in concept_ids
        ]


    total = len(
        all_concepts
    )


    print(
        f"[Prerequisite Processing] "
        f"{total} concept(s) to process."
    )


    # =====================================================
    # 1. Restore all completed checkpoints first
    # =====================================================

    pending_concepts = []


    for index, concept in enumerate(
        all_concepts,
        start=1
    ):

        print(
            f"[Prerequisite Processing] "
            f"{index}/{total} -> "
            f"{concept.name}"
        )


        restored = _restore_checkpoint(
            concept=concept,
            registry=registry
        )


        if restored:
            continue


        pending_concepts.append(
            concept
        )


    # =====================================================
    # Nothing new to process
    # =====================================================

    if not pending_concepts:

        print(
            "[Prerequisite Processing] "
            "All concepts restored from checkpoints."
        )

        return registry


    print()

    print(
        "[Prerequisite Processing] "
        f"{len(pending_concepts)} concept(s) "
        f"require LLM processing."
    )


    estimated_batches = (
        len(pending_concepts)
        + batch_size
        - 1
    ) // batch_size


    print(
        "[Prerequisite Processing] "
        f"Batch size: {batch_size}"
    )


    print(
        "[Prerequisite Processing] "
        f"Estimated LLM calls: "
        f"{estimated_batches}"
    )


    # =====================================================
    # 2. Process pending concepts in batches
    # =====================================================

    for batch_start in range(
        0,
        len(pending_concepts),
        batch_size
    ):

        batch = pending_concepts[
            batch_start:
            batch_start + batch_size
        ]


        batch_number = (
            batch_start // batch_size
        ) + 1


        print()

        print(
            "=" * 60
        )

        print(
            f"[Prerequisite Batch] "
            f"{batch_number}/"
            f"{estimated_batches}"
        )

        print(
            "[Prerequisite Batch] "
            f"Concepts: "
            f"{', '.join(c.name for c in batch)}"
        )

        print(
            "=" * 60
        )


        # =================================================
        # ONE LLM call for entire batch
        # =================================================

        try:

            batch_results = (
                extract_prerequisites_for_batch(
                    concepts=batch,
                    registry=registry,
                    top_k=top_k
                )
            )


        except LLMUnavailableError:

            print(
                "[Prerequisite Batch] "
                "All LLM providers unavailable."
            )

            print(
                "[Prerequisite Batch] "
                "Current batch will NOT be checkpointed."
            )

            print(
                "[Prerequisite Batch] "
                "Completed earlier batches are preserved."
            )

            raise


        except RateLimitError:

            print(
                "[Prerequisite Batch] "
                "Provider rate limit reached."
            )

            print(
                "[Prerequisite Batch] "
                "Current batch will NOT be checkpointed."
            )

            raise


        # =================================================
        # 3. Validate/apply returned edges locally
        # =================================================

        for concept in batch:

            proposed_edges = (
                batch_results.get(
                    concept.concept_id,
                    []
                )
            )


            successful_prerequisites = []


            for edge in proposed_edges:

                prerequisite_id = edge.get(
                    "prerequisite_id"
                )


                confidence = edge.get(
                    "confidence",
                    0
                )


                prerequisite = (
                    registry.get_concept(
                        prerequisite_id
                    )
                )


                if not prerequisite:

                    print(
                        "  x Missing prerequisite "
                        f"concept: "
                        f"{prerequisite_id}"
                    )

                    continue


                print(
                    f"  ? Candidate: "
                    f"{prerequisite.name} -> "
                    f"{concept.name} "
                    f"(confidence={confidence:.2f})"
                )


                # -----------------------------------------
                # Registry performs:
                #
                # self-edge protection
                # duplicate protection
                # cycle protection
                # -----------------------------------------

                added = registry.add_prerequisite(
                    concept.concept_id,
                    prerequisite_id
                )


                current_concept = (
                    registry.get_concept(
                        concept.concept_id
                    )
                )


                already_present = (
                    current_concept is not None
                    and prerequisite_id
                    in current_concept.prerequisites
                )


                if added:

                    print(
                        f"  + Added: "
                        f"{prerequisite.name} -> "
                        f"{concept.name}"
                    )


                    successful_prerequisites.append(
                        prerequisite_id
                    )


                elif already_present:

                    successful_prerequisites.append(
                        prerequisite_id
                    )


                else:

                    print(
                        f"  x Rejected by graph "
                        f"validation: "
                        f"{prerequisite.name} -> "
                        f"{concept.name}"
                    )


            # =================================================
            # Save one checkpoint per target concept
            #
            # Empty prerequisite lists are valid completed
            # results.
            # =================================================

            save_prerequisite_checkpoint(
                concept_id=concept.concept_id,
                concept_name=concept.name,
                prerequisites=successful_prerequisites
            )


        print(
            f"[Prerequisite Batch] "
            f"Batch {batch_number} complete."
        )


    print()

    print(
        "[Prerequisite Processing] "
        "All prerequisite batches complete."
    )


    return registry