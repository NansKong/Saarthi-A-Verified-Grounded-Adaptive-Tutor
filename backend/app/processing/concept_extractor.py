import re

from app.llm.text_llm import (
    generate_json
)


def slugify_concept(
    concept_name: str
) -> str:
    """
    Convert a concept name into a stable concept ID.

    Example:

        "Gradient Descent"
        ->
        "gradient_descent"
    """

    value = concept_name.strip().lower()

    value = re.sub(
        r"[^a-z0-9\s_-]",
        "",
        value
    )

    value = re.sub(
        r"[\s-]+",
        "_",
        value
    )

    value = re.sub(
        r"_+",
        "_",
        value
    )


    return value.strip("_")


def _build_unit_content(
    unit
) -> str:

    sections = []


    if (
        getattr(
            unit,
            "text",
            None
        )
        and unit.text.strip()
    ):

        sections.append(
            f"""
TEXT CONTENT:

{unit.text.strip()}
"""
        )


    visual_description = getattr(
        unit,
        "visual_description",
        None
    )


    if (
        visual_description
        and visual_description.strip()
    ):

        sections.append(
            f"""
VISUAL DESCRIPTION:

{visual_description.strip()}
"""
        )


    return "\n".join(
        sections
    ).strip()


def extract_concepts_from_unit(
    unit
) -> dict:
    """
    Extract topic, subtopic, and educational
    concepts from a ContentUnit.
    """

    content = _build_unit_content(
        unit
    )


    if not content:

        return {
            "topic": None,
            "subtopic": None,
            "concepts": [],
            "concept_ids": []
        }


    prompt = f"""
Analyze the following educational material.

CONTENT:

{content}


Identify:

1. The main topic.
2. The most specific useful subtopic.
3. The important educational concepts explicitly
   supported by the material.

Concepts should be:

- meaningful educational ideas,
- suitable for building a tutoring knowledge graph,
- grounded in the supplied content,
- concise canonical names,
- not sentences,
- not generic filler words,
- not hallucinated.

Examples of good concepts:

"Gradient Descent"
"Loss Function"
"Neural Network"
"Backpropagation"
"Linear Regression"
"Cross Validation"

Avoid overly broad or meaningless concepts unless they
are genuinely important to the content.

Extract at most 8 concepts.

Return ONLY valid JSON.

Required format:

{{
    "topic": "Machine Learning",
    "subtopic": "Optimization",
    "concepts": [
        "Gradient",
        "Gradient Descent",
        "Loss Function"
    ]
}}
"""


    system_prompt = (
        "You extract structured educational concepts "
        "from learning material. "
        "Only extract concepts supported by the provided "
        "content. Do not hallucinate information. "
        "Return ONLY valid JSON."
    )


    # -------------------------------------------------
    # Groq -> Gemini fallback happens here
    # -------------------------------------------------

    try:

        result = generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    except Exception as exc:

        print(
            f"[Concept Extractor] "
            f"All LLM providers failed for "
            f"{getattr(unit, 'unit_id', 'unknown_unit')}: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        # Let semantic_processor know that this unit
        # did NOT finish successfully.
        raise


    # -------------------------------------------------
    # Topic
    # -------------------------------------------------

    topic = result.get(
        "topic"
    )


    if topic is not None:

        if not isinstance(
            topic,
            str
        ):
            topic = None

        elif not topic.strip():
            topic = None

        else:
            topic = topic.strip()


    # -------------------------------------------------
    # Subtopic
    # -------------------------------------------------

    subtopic = result.get(
        "subtopic"
    )


    if subtopic is not None:

        if not isinstance(
            subtopic,
            str
        ):
            subtopic = None

        elif not subtopic.strip():
            subtopic = None

        else:
            subtopic = subtopic.strip()


    # -------------------------------------------------
    # Concepts
    # -------------------------------------------------

    raw_concepts = result.get(
        "concepts",
        []
    )


    if not isinstance(
        raw_concepts,
        list
    ):

        raw_concepts = []


    concepts = []
    concept_ids = []

    seen_ids = set()


    for concept in raw_concepts:

        if not isinstance(
            concept,
            str
        ):
            continue


        concept = concept.strip()


        if not concept:
            continue


        concept_id = slugify_concept(
            concept
        )


        if not concept_id:
            continue


        if concept_id in seen_ids:
            continue


        seen_ids.add(
            concept_id
        )

        concepts.append(
            concept
        )

        concept_ids.append(
            concept_id
        )


        if len(concepts) >= 8:
            break


    return {
        "topic":
            topic,

        "subtopic":
            subtopic,

        "concepts":
            concepts,

        "concept_ids":
            concept_ids
    }


# -------------------------------------------------
# Compatibility alias
#
# If another module currently imports
# extract_concepts instead of
# extract_concepts_from_unit, both will work.
# -------------------------------------------------

def extract_concepts(
    unit
) -> dict:

    return extract_concepts_from_unit(
        unit
    )


def extract_semantic_metadata(
    unit
) -> dict:
    """
    Backward-compatible wrapper used by
    concept_registry_processor.py.
    """

    return extract_concepts_from_unit(
        unit
    )