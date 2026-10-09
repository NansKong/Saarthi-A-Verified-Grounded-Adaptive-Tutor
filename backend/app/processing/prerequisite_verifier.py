from app.llm.text_llm import (
    generate_json
)


def verify_prerequisite_relationship(
    prerequisite_name: str,
    target_name: str
) -> bool:
    """
    Strictly verify whether:

        prerequisite_name -> target_name

    is a genuine DIRECT educational prerequisite.
    """


    prompt = f"""
You are validating prerequisite edges for an adaptive
education knowledge graph.

PROPOSED EDGE:

{prerequisite_name} -> {target_name}

Meaning:

A student should understand "{prerequisite_name}"
BEFORE learning "{target_name}".

Your job is to be VERY CONSERVATIVE.

A concept is a DIRECT prerequisite only when understanding
the target would normally require prior understanding of
the prerequisite.

Do NOT accept an edge simply because:

- the concepts are related,
- they belong to the same subject,
- they are often taught together,
- they use similar terminology,
- one concept could optionally help explain the other.

Examples:

Gradient -> Gradient Descent
DIRECT prerequisite.

Neural Network -> Backpropagation
DIRECT prerequisite.

Linear Regression -> Neural Network
NOT a direct prerequisite.

Logistic Regression -> Neural Network
NOT a direct prerequisite.

Gradient -> Neural Network
NOT a direct prerequisite.

Gradient Descent -> Learning Rate
WRONG direction.

Learning Rate -> Gradient Descent
may be related, but is not necessarily a required
direct prerequisite.

Loss Function -> Backpropagation
may be related but should only be accepted if it is
genuinely required before learning Backpropagation.

Choose exactly ONE relationship:

"DIRECT_PREREQUISITE"
"REVERSE_DIRECTION"
"RELATED_ONLY"
"UNRELATED"

Also provide confidence between 0 and 1.

Return ONLY valid JSON.

Required format:

{{
    "relationship": "DIRECT_PREREQUISITE",
    "confidence": 0.95
}}
"""


    system_prompt = (
        "You validate direct educational prerequisite "
        "relationships with very high precision. "
        "When uncertain, reject the prerequisite edge. "
        "Return ONLY valid JSON."
    )


    # -------------------------------------------------
    # Groq -> Gemini fallback is handled automatically
    # inside generate_json()
    # -------------------------------------------------

    try:

        result = generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    except Exception as exc:

        print(
            "[Prerequisite Verifier] "
            f"All LLM providers failed while verifying "
            f"{prerequisite_name} -> {target_name}: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        # Important for checkpoint logic:
        # do not mark an unfinished concept as complete.
        raise


    # -------------------------------------------------
    # Validate response
    # -------------------------------------------------

    relationship = result.get(
        "relationship"
    )


    try:

        confidence = float(
            result.get(
                "confidence",
                0.0
            )
        )


    except (
        TypeError,
        ValueError
    ):

        confidence = 0.0


    # -------------------------------------------------
    # Strict acceptance threshold
    # -------------------------------------------------

    return (
        relationship
        == "DIRECT_PREREQUISITE"
        and confidence >= 0.85
    )