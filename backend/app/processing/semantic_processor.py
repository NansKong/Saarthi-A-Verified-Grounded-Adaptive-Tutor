from groq import RateLimitError

from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.processing.concept_registry_processor import (
    process_unit_concepts
)

from app.checkpoints.checkpoint_service import (
    load_semantic_checkpoint,
    save_semantic_checkpoint
)

from app.llm.text_llm import (
    LLMUnavailableError
)


def enrich_content_units(
    units,
    registry: ConceptRegistry
):

    total = len(
        units
    )


    for index, unit in enumerate(
        units,
        start=1
    ):

        print(
            f"[Semantic Processing] "
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


        # =================================================
        # Skip empty unit
        # =================================================

        if (
            not text_content.strip()
            and
            not visual_content.strip()
        ):

            print(
                f"[Semantic Processing] "
                f"Skipping empty unit: "
                f"{unit.unit_id}"
            )

            continue


        # =================================================
        # Restore semantic checkpoint
        # =================================================

        checkpoint = (
            load_semantic_checkpoint(
                unit.unit_id
            )
        )


        if (
            checkpoint
            and
            checkpoint.get(
                "status"
            )
            == "completed"
        ):

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
                f"[Semantic Processing] "
                f"Checkpoint restored: "
                f"{unit.unit_id}"
            )


            # ---------------------------------------------
            # Restore concepts into active registry
            # ---------------------------------------------

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


            continue


        # =================================================
        # Process new semantic unit
        # =================================================

        try:

            process_unit_concepts(
                unit=unit,
                registry=registry
            )


        except LLMUnavailableError:

            print(
                f"[Semantic Processing] "
                f"All LLM providers unavailable "
                f"while processing "
                f"{unit.unit_id}."
            )

            print(
                "[Semantic Processing] "
                "Current unit will NOT be checkpointed."
            )

            print(
                "[Semantic Processing] "
                "Completed checkpoints are preserved."
            )

            raise


        except RateLimitError:

            print(
                f"[Semantic Processing] "
                f"Rate limit reached at "
                f"{unit.unit_id}."
            )

            print(
                "[Semantic Processing] "
                "Current unit will NOT be checkpointed."
            )

            raise


        except Exception as exc:

            print(
                f"[Semantic Processing Error] "
                f"{unit.unit_id}: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            raise


        # =================================================
        # Save completed unit
        # =================================================

        save_semantic_checkpoint(
            unit_id=unit.unit_id,
            topic=unit.topic,
            subtopic=unit.subtopic,
            concept_ids=list(
                unit.concept_ids
            )
        )


    return units