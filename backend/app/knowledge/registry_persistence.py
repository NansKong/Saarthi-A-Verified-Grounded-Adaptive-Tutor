from app.knowledge.concept_registry import (
    ConceptRegistry
)

from app.knowledge.graph_validator import (
    validate_graph
)

from app.vectorstore.qdrant_service import (
    qdrant_service,
    CONCEPT_COLLECTION
)


def _load_all_concept_payloads() -> list[dict]:
    """
    Read every persisted concept payload from Qdrant.

    Uses pagination so this continues working when the
    knowledge base grows beyond a single page.
    """

    payloads = []

    offset = None


    while True:

        records, next_offset = (
            qdrant_service.client.scroll(
                collection_name=CONCEPT_COLLECTION,

                limit=100,

                offset=offset,

                with_payload=True,

                with_vectors=False
            )
        )


        for record in records:

            payload = (
                record.payload
                or {}
            )


            if not payload:
                continue


            payloads.append(
                payload
            )


        if next_offset is None:
            break


        offset = next_offset


    return payloads


def restore_registry_from_qdrant(
    registry: ConceptRegistry
) -> dict:
    """
    Rebuild the in-memory ConceptRegistry from Qdrant.

    Two-pass restoration:

    Pass 1:
        Restore every concept node.

    Pass 2:
        Restore prerequisite edges.

    This guarantees prerequisite targets exist before
    edges are added.
    """

    print()
    print(
        "[Registry Restore] "
        "Loading concepts from Qdrant..."
    )


    try:

        payloads = (
            _load_all_concept_payloads()
        )


    except Exception as exc:

        print(
            "[Registry Restore] "
            f"Failed to read Qdrant: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )


        return {
            "concepts_restored": 0,
            "edges_restored": 0,
            "edges_skipped": 0,
            "has_cycles": False,
            "cycle_nodes": [],
            "status": "failed"
        }


    # =====================================================
    # Empty Qdrant collection
    # =====================================================

    if not payloads:

        print(
            "[Registry Restore] "
            "No persisted concepts found."
        )


        return {
            "concepts_restored": 0,
            "edges_restored": 0,
            "edges_skipped": 0,
            "has_cycles": False,
            "cycle_nodes": [],
            "status": "empty"
        }


    # =====================================================
    # Clear stale in-memory state
    #
    # Qdrant becomes the persistent source of truth
    # when the server starts.
    # =====================================================

    registry.concepts.clear()


    # =====================================================
    # PASS 1 — restore concept nodes
    # =====================================================

    concepts_restored = 0


    for payload in payloads:

        concept_id = (
            payload.get(
                "concept_id"
            )
        )

        name = (
            payload.get(
                "name"
            )
        )


        if not concept_id or not name:

            print(
                "[Registry Restore] "
                "Skipping malformed concept payload."
            )

            continue


        aliases = (
            payload.get(
                "aliases",
                []
            )
            or []
        )

        topic = (
            payload.get(
                "topic"
            )
        )

        subtopic = (
            payload.get(
                "subtopic"
            )
        )

        evidence_units = (
            payload.get(
                "evidence_units",
                []
            )
            or []
        )


        record = registry.add_concept(
            concept_id=concept_id,

            name=name,

            topic=topic,

            subtopic=subtopic,

            aliases=list(
                dict.fromkeys(
                    aliases
                )
            )
        )


        # ---------------------------------------------
        # Restore all evidence-unit links
        # ---------------------------------------------

        record.evidence_units = list(
            dict.fromkeys(
                evidence_units
            )
        )


        concepts_restored += 1


    print(
        "[Registry Restore] "
        f"{concepts_restored} "
        f"concept(s) restored."
    )


    # =====================================================
    # PASS 2 — restore prerequisite edges
    # =====================================================

    edges_restored = 0
    edges_skipped = 0


    for payload in payloads:

        concept_id = (
            payload.get(
                "concept_id"
            )
        )


        if not concept_id:
            continue


        prerequisites = (
            payload.get(
                "prerequisites",
                []
            )
            or []
        )


        for prerequisite_id in prerequisites:

            # -----------------------------------------
            # Missing/stale prerequisite node
            # -----------------------------------------

            if not registry.get_concept(
                prerequisite_id
            ):

                print(
                    "[Registry Restore] "
                    f"Skipping stale prerequisite: "
                    f"{prerequisite_id} -> "
                    f"{concept_id}"
                )

                edges_skipped += 1

                continue


            # -----------------------------------------
            # Registry validation protects against:
            #
            # - self edges
            # - duplicates
            # - cycles
            # -----------------------------------------

            added = (
                registry.add_prerequisite(
                    concept_id=concept_id,

                    prerequisite_id=(
                        prerequisite_id
                    )
                )
            )


            if added:

                edges_restored += 1

            else:

                edges_skipped += 1


    print(
        "[Registry Restore] "
        f"{edges_restored} "
        f"prerequisite edge(s) restored."
    )


    if edges_skipped:

        print(
            "[Registry Restore] "
            f"{edges_skipped} "
            f"invalid/stale edge(s) skipped."
        )


    # =====================================================
    # Validate restored graph
    # =====================================================

    validation = (
        validate_graph(
            registry
        )
    )


    has_cycles = (
        validation.get(
            "has_cycles",
            False
        )
    )

    cycle_nodes = (
        validation.get(
            "cycle_nodes",
            []
        )
    )


    print(
        "[Registry Restore] "
        f"Graph valid: "
        f"{not has_cycles}"
    )


    if has_cycles:

        print(
            "[Registry Restore] "
            f"Cycle nodes: "
            f"{cycle_nodes}"
        )


    print(
        "[Registry Restore] "
        "Startup registry restoration complete."
    )

    print()


    return {
        "concepts_restored":
            concepts_restored,

        "edges_restored":
            edges_restored,

        "edges_skipped":
            edges_skipped,

        "has_cycles":
            has_cycles,

        "cycle_nodes":
            cycle_nodes,

        "status":
            "completed"
    }