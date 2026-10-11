from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConceptRecord:
    concept_id: str
    name: str

    aliases: List[str] = field(default_factory=list)

    topic: str | None = None
    subtopic: str | None = None

    evidence_units: List[str] = field(default_factory=list)

    prerequisites: List[str] = field(default_factory=list)

    embedding: List[float] | None = None


class ConceptRegistry:

    def __init__(self):
        self.concepts: Dict[str, ConceptRecord] = {}


    def add_concept(
        self,
        concept_id: str,
        name: str,
        topic: str | None = None,
        subtopic: str | None = None,
        aliases: List[str] | None = None,
        evidence_unit: str | None = None,
    ) -> ConceptRecord:

        if concept_id in self.concepts:

            record = self.concepts[concept_id]

            if (
                evidence_unit
                and evidence_unit not in record.evidence_units
            ):
                record.evidence_units.append(
                    evidence_unit
                )

            if aliases:
                for alias in aliases:
                    if alias not in record.aliases:
                        record.aliases.append(
                            alias
                        )

            return record


        record = ConceptRecord(
            concept_id=concept_id,
            name=name,
            topic=topic,
            subtopic=subtopic,
            aliases=aliases or [],
            evidence_units=(
                [evidence_unit]
                if evidence_unit
                else []
            ),
            prerequisites=[]
        )

        self.concepts[concept_id] = record

        return record


    def add_prerequisite(
        self,
        concept_id: str,
        prerequisite_id: str
    ) -> bool:

        concept = self.get_concept(
            concept_id
        )

        prerequisite = self.get_concept(
            prerequisite_id
        )


        # Invalid concept
        if not concept or not prerequisite:
            return False


        # Self prerequisite
        if prerequisite_id == concept_id:
            return False


        # Duplicate edge
        if prerequisite_id in concept.prerequisites:
            return False


        # Import here to avoid circular import
        from app.knowledge.graph_validator import (
            creates_cycle
        )


        # Reject cycle
        if creates_cycle(
            registry=self,
            concept_id=concept_id,
            prerequisite_id=prerequisite_id
        ):

            print(
                f"[Graph Validation] Rejected cycle: "
                f"{prerequisite_id} -> {concept_id}"
            )

            return False


        # Add valid prerequisite
        concept.prerequisites.append(
            prerequisite_id
        )

        return True


    def get_concept(
        self,
        concept_id: str
    ) -> ConceptRecord | None:

        return self.concepts.get(
            concept_id
        )


    def get_all_concepts(
        self
    ) -> List[ConceptRecord]:

        return list(
            self.concepts.values()
        )


    def to_dict(self):

        return [
            {
                "concept_id": record.concept_id,
                "name": record.name,
                "aliases": record.aliases,
                "topic": record.topic,
                "subtopic": record.subtopic,
                "evidence_units": record.evidence_units,
                "prerequisites": record.prerequisites
            }
            for record in self.get_all_concepts()
        ]