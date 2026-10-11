from app.knowledge.concept_registry import ConceptRegistry


def build_adjacency(
    registry: ConceptRegistry
) -> dict[str, list[str]]:
    """
    Build graph in prerequisite -> dependent direction.

    Example:

    gradient_descent.prerequisites = ["gradient"]

    becomes:

    gradient -> gradient_descent
    """

    adjacency = {
        concept.concept_id: []
        for concept in registry.get_all_concepts()
    }

    for concept in registry.get_all_concepts():

        for prerequisite_id in concept.prerequisites:

            if prerequisite_id in adjacency:
                adjacency[prerequisite_id].append(
                    concept.concept_id
                )

    return adjacency


def has_path(
    adjacency: dict[str, list[str]],
    start: str,
    target: str
) -> bool:

    visited = set()
    stack = [start]

    while stack:

        current = stack.pop()

        if current == target:
            return True

        if current in visited:
            continue

        visited.add(current)

        stack.extend(
            adjacency.get(current, [])
        )

    return False


def creates_cycle(
    registry: ConceptRegistry,
    concept_id: str,
    prerequisite_id: str
) -> bool:
    """
    Proposed edge:

        prerequisite_id -> concept_id

    creates a cycle if concept_id can already
    reach prerequisite_id.
    """

    if concept_id == prerequisite_id:
        return True

    adjacency = build_adjacency(
        registry
    )

    return has_path(
        adjacency=adjacency,
        start=concept_id,
        target=prerequisite_id
    )


def validate_graph(
    registry: ConceptRegistry
) -> dict:
    """
    Validate the complete prerequisite graph.

    Returns:
        concept_count
        edge_count
        has_cycles
        cycle_nodes
    """

    adjacency = build_adjacency(
        registry
    )

    visited = set()
    active = set()

    cycle_nodes = set()


    def dfs(node: str):

        if node in active:
            cycle_nodes.add(node)
            return

        if node in visited:
            return

        visited.add(node)
        active.add(node)

        for neighbor in adjacency.get(
            node,
            []
        ):
            dfs(neighbor)

        active.remove(node)


    for node in adjacency:

        if node not in visited:
            dfs(node)


    edge_count = sum(
        len(edges)
        for edges in adjacency.values()
    )


    return {
        "concept_count": len(adjacency),
        "edge_count": edge_count,
        "has_cycles": len(cycle_nodes) > 0,
        "cycle_nodes": list(cycle_nodes)
    }