from app.knowledge.concept_registry import ConceptRegistry


def get_direct_prerequisites(
    concept_id: str,
    registry: ConceptRegistry
) -> list[str]:

    concept = registry.get_concept(
        concept_id
    )

    if not concept:
        return []

    return list(
        concept.prerequisites
    )


def get_all_prerequisites(
    concept_id: str,
    registry: ConceptRegistry
) -> list[str]:

    visited = set()
    ordered = []


    def dfs(current_id: str):

        concept = registry.get_concept(
            current_id
        )

        if not concept:
            return


        for prerequisite_id in concept.prerequisites:

            if prerequisite_id in visited:
                continue

            visited.add(
                prerequisite_id
            )

            dfs(
                prerequisite_id
            )

            ordered.append(
                prerequisite_id
            )


    dfs(
        concept_id
    )

    return ordered


def get_learning_order(
    concept_id: str,
    registry: ConceptRegistry
) -> list[str]:

    prerequisites = get_all_prerequisites(
        concept_id,
        registry
    )

    if registry.get_concept(concept_id):

        prerequisites.append(
            concept_id
        )

    return prerequisites


def get_direct_dependents(
    concept_id: str,
    registry: ConceptRegistry
) -> list[str]:

    dependents = []

    for concept in registry.get_all_concepts():

        if concept_id in concept.prerequisites:

            dependents.append(
                concept.concept_id
            )

    return dependents


def get_all_dependents(
    concept_id: str,
    registry: ConceptRegistry
) -> list[str]:

    visited = set()
    ordered = []


    def dfs(current_id: str):

        direct_dependents = (
            get_direct_dependents(
                current_id,
                registry
            )
        )

        for dependent_id in direct_dependents:

            if dependent_id in visited:
                continue

            visited.add(
                dependent_id
            )

            ordered.append(
                dependent_id
            )

            dfs(
                dependent_id
            )


    dfs(
        concept_id
    )

    return ordered


def get_learning_path_details(
    concept_id: str,
    registry: ConceptRegistry
) -> list[dict]:

    learning_order = get_learning_order(
        concept_id,
        registry
    )

    details = []


    for current_id in learning_order:

        concept = registry.get_concept(
            current_id
        )

        if not concept:
            continue


        details.append(
            {
                "concept_id":
                    concept.concept_id,

                "name":
                    concept.name,

                "topic":
                    concept.topic,

                "subtopic":
                    concept.subtopic,

                "prerequisites":
                    list(
                        concept.prerequisites
                    )
            }
        )


    return details