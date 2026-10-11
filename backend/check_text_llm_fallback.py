from app.llm.text_llm import generate_json


result = generate_json(
    prompt="""
Return this exact structure:

{
    "topic": "Machine Learning",
    "concepts": [
        "Gradient Descent",
        "Loss Function"
    ]
}
""",
    system_prompt=(
        "Return ONLY valid JSON."
    )
)


print(result)