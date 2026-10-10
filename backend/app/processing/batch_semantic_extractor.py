import json

from app.llm.text_llm import (
    generate_json
)


def _get_unit_content(
    unit
) -> str:

    parts = []

    text = getattr(
        unit,
        "text",
        None
    )

    visual_description = getattr(
        unit,
        "visual_description",
        None
    )


    if text and text.strip():

        parts.append(
            f"TEXT:\n{text.strip()}"
        )


    if (
        visual_description
        and visual_description.strip()
    ):

        parts.append(
            "VISUAL DESCRIPTION:\n"
            f"{visual_description.strip()}"
        )


    return "\n\n".join(
        parts
    ).strip()


def extract_semantic_metadata_batch(
    units: list
) -> dict[str, dict]:
    """
    Extract semantic metadata for several ContentUnits
    using ONE LLM call.

    Returns:

    {
        "unit_id": {
            "topic": "...",
            "subtopic": "...",
            "concepts": [...]
        }
    }
    """

    payload = []


    for unit in units:

        content = _get_unit_content(
            unit
        )


        if not content:
            continue


        payload.append(
            {
                "unit_id":
                    unit.unit_id,

                "content":
                    content
            }
        )


    if not payload:

        return {}


    prompt = f"""
You are extracting structured educational metadata
from multiple course-content units.

For EACH unit identify:

1. Main topic
2. Specific useful subtopic
3. Important educational concepts

Concepts must:

- be grounded in the supplied unit
- be concise canonical educational concepts
- not be complete sentences
- avoid generic filler terms
- avoid unnecessary duplicates
- contain at most 8 concepts per unit

Important:

Each unit must remain separate.
Do not mix concepts between units.

INPUT UNITS:

{json.dumps(payload, indent=2)}


Return ONLY valid JSON.

Required structure:

{{
    "results": [
        {{
            "unit_id": "unit_1",
            "topic": "Machine Learning",
            "subtopic": "Optimization",
            "concepts": [
                "Gradient Descent",
                "Gradient",
                "Loss Function"
            ]
        }}
    ]
}}
"""


    result = generate_json(
        prompt=prompt,

        system_prompt=(
            "You extract structured educational "
            "metadata from multiple learning-content "
            "units. Keep every unit separate and only "
            "extract concepts grounded in its content. "
            "Return only valid JSON."
        )
    )


    raw_results = result.get(
        "results",
        []
    )


    final_results = {}


    if not isinstance(
        raw_results,
        list
    ):

        return final_results


    valid_unit_ids = {
        unit.unit_id
        for unit in units
    }


    for item in raw_results:

        if not isinstance(
            item,
            dict
        ):
            continue


        unit_id = item.get(
            "unit_id"
        )


        if unit_id not in valid_unit_ids:
            continue


        topic = item.get(
            "topic"
        )

        subtopic = item.get(
            "subtopic"
        )

        concepts = item.get(
            "concepts",
            []
        )


        if not isinstance(
            concepts,
            list
        ):

            concepts = []


        clean_concepts = []

        seen = set()


        for concept in concepts:

            if not isinstance(
                concept,
                str
            ):
                continue


            concept = concept.strip()


            if not concept:
                continue


            normalized = (
                concept.lower()
            )


            if normalized in seen:
                continue


            seen.add(
                normalized
            )

            clean_concepts.append(
                concept
            )


            if len(
                clean_concepts
            ) >= 8:
                break


        final_results[
            unit_id
        ] = {
            "topic":
                topic.strip()
                if isinstance(
                    topic,
                    str
                )
                and topic.strip()
                else None,

            "subtopic":
                subtopic.strip()
                if isinstance(
                    subtopic,
                    str
                )
                and subtopic.strip()
                else None,

            "concepts":
                clean_concepts
        }


    return final_results