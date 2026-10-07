import os
import base64
import mimetypes

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found in the environment."
    )


client = Groq(api_key=API_KEY)


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


def describe_educational_image(image_path: str) -> str:
    base64_image = encode_image(image_path)

    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type:
        mime_type = "image/png"

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Analyze this image as part of educational course material.

Describe only academically useful information visible in the image.

Focus on:
- diagrams
- graphs
- charts
- equations
- labeled components
- workflows
- conceptual relationships

Ignore:
- logos
- decorative elements
- borders
- styling

Return a concise description suitable for retrieval in an AI knowledge base.

If the image does not contain meaningful educational information,
return exactly:

NOT_EDUCATIONAL
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":
                            f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],

        temperature=0.1
    )

    return response.choices[0].message.content.strip()