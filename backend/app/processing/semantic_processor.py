from groq import (
    RateLimitError
)

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.batch_semantic_extractor import (
    extract_semantic_metadata_batch
)

from app.processing.concept_registry_processor import (
    apply_semantic_metadata_batch
)

from app.checkpoints.checkpoint_service import (
    load_semantic_checkpoint,
    save_semantic_checkpoint
)

from app.llm.text_llm import (
    LLMUnavailableError
)


def _restore_checkpoint(
    unit,
    registry: ConceptRegistry
) -> bool:

    checkpoint = (
        load_semantic_checkpoint(
            unit.unit_id
        )
    )


    if not (
        checkpoint
        and
        checkpoint.get(
            "status"
        )
        == "completed"
    ):

        return False


    unit.topic = (
        checkpoint.get(
            "topic"
        )
    )

    unit.subtopic = (
        checkpoint.get(
            "subtopic"
        )
    )

    unit.concept_ids = (
        checkpoint.get(
            "concept_ids",
            []
        )
    )


    print(
        "[Semantic Processing] "
        f"Checkpoint restored: "
        f"{unit.unit_id}"
    )


    # =====================================================
    # Rebuild active registry
    # =====================================================

    for concept_id in unit.concept_ids:

        existing = (
            registry.get_concept(
                concept_id
            )
        )


        if existing:

            if (
                unit.unit_id
                not in existing.evidence_units
            ):

                existing.evidence_units.append(
                    unit.unit_id
                )

            continue


        readable_name = (
            concept_id
            .replace(
                "_",
                " "
            )
            .title()
        )


        registry.add_concept(
            concept_id=concept_id,
            name=readable_name,
            topic=unit.topic,
            subtopic=unit.subtopic,
            evidence_unit=unit.unit_id
        )


    return True


def enrich_content_units(
    units,
    registry: ConceptRegistry,
    batch_size: int = 5
):

    total = len(
        units
    )


    pending_units = []


    # =====================================================
    # Restore checkpoints
    # =====================================================

    for index, unit in enumerate(
        units,
        start=1
    ):

        print(
            "[Semantic Processing] "
            f"{index}/{total} -> "
            f"{unit.unit_id}"
        )


        text_content = (
            unit.text
            if unit.text
            else ""
        )

        visual_content = (
            unit.visual_description
            if unit.visual_description
            else ""
        )


        if (
            not text_content.strip()
            and
            not visual_content.strip()
        ):

            print(
                "[Semantic Processing] "
                f"Skipping empty unit: "
                f"{unit.unit_id}"
            )

            continue


        if _restore_checkpoint(
            unit=unit,
            registry=registry
        ):

            continue


        pending_units.append(
            unit
        )


    if not pending_units:

        print(
            "[Semantic Processing] "
            "All units restored from checkpoints."
        )

        return units


    estimated_batches = (
        len(pending_units)
        + batch_size
        - 1
    ) // batch_size


    print()

    print(
        "[Semantic Processing] "
        f"{len(pending_units)} "
        "unit(s) require LLM processing."
    )

    print(
        "[Semantic Processing] "
        f"Batch size: {batch_size}"
    )

    print(
        "[Semantic Processing] "
        f"Estimated semantic extraction calls: "
        f"{estimated_batches}"
    )


    # =====================================================
    # Process batches
    # =====================================================

    for batch_start in range(
        0,
        len(pending_units),
        batch_size
    ):

        batch = (
            pending_units[
                batch_start:
                batch_start + batch_size
            ]
        )


        batch_number = (
            batch_start // batch_size
        ) + 1


        print()

        print(
            "=" * 60
        )

        print(
            "[Semantic Batch] "
            f"{batch_number}/"
            f"{estimated_batches}"
        )

        print(
            "[Semantic Batch] "
            f"{len(batch)} unit(s)"
        )

        print(
            "=" * 60
        )


        try:

            # =============================================
            # CALL 1 — semantic extraction
            # =============================================

            metadata_by_unit = (
                extract_semantic_metadata_batch(
                    batch
                )
            )


            # =============================================
            # CALL 2 MAXIMUM — concept normalization
            #
            # Local matches will not need an LLM.
            # =============================================

            apply_semantic_metadata_batch(
                units=batch,
                metadata_by_unit=metadata_by_unit,
                registry=registry
            )


        except LLMUnavailableError:

            print(
                "[Semantic Batch] "
                "All LLM providers unavailable."
            )

            print(
                "[Semantic Batch] "
                "Current batch will NOT "
                "be checkpointed."
            )

            print(
                "[Semantic Batch] "
                "Earlier completed batches "
                "are preserved."
            )

            raise


        except RateLimitError:

            print(
                "[Semantic Batch] "
                "Provider rate limit reached."
            )

            raise


        # =================================================
        # Only checkpoint successful units
        # =================================================

        for unit in batch:

            if (
                unit.unit_id
                not in metadata_by_unit
            ):

                print(
                    "[Semantic Batch] "
                    f"No metadata returned for "
                    f"{unit.unit_id}."
                )

                continue


            save_semantic_checkpoint(
                unit_id=unit.unit_id,
                topic=unit.topic,
                subtopic=unit.subtopic,
                concept_ids=list(
                    unit.concept_ids
                )
            )


        print(
            "[Semantic Batch] "
            f"Batch {batch_number} complete."
        )


    print()

    print(
        "[Semantic Processing] "
        "All semantic batches complete."
    )


    return units