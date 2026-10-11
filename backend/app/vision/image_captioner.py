import base64
import mimetypes
import os

from dotenv import load_dotenv

from groq import (
    Groq,
    RateLimitError
)

from google import genai
from google.genai import types

from app.llm.text_llm import (
    LLMUnavailableError,
    wait_for_gemini_slot,
    get_retry_after_seconds
)


load_dotenv()


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL"
) or os.getenv(
    "model"
)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_VISION_MODEL = os.getenv(
    "GEMINI_VISION_MODEL",
    os.getenv(
        "GEMINI_TEXT_MODEL",
        "gemini-3.8-flash"
    )
)


groq_client = None

if GROQ_API_KEY:

    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


gemini_client = None

if GEMINI_API_KEY:

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


VISION_PROMPT = """
Analyze this image as part of an educational
knowledge base.

Describe ONLY academically useful content.

Focus on:

- diagrams
- charts
- graphs
- equations
- formulas
- algorithms
- workflows
- labeled structures
- tables
- technical illustrations
- important written instructional content
- relationships between concepts

Ignore:

- university/company logos
- branding
- watermarks
- decorative backgrounds
- instructor appearance
- irrelevant room details

Return a concise retrieval-friendly description.

If the image contains no meaningful educational
information, return exactly:

NOT_EDUCATIONAL
"""


def encode_image(
    image_path: str
) -> str:

    with open(
        image_path,
        "rb"
    ) as file:

        return (
            base64.b64encode(
                file.read()
            )
            .decode(
                "utf-8"
            )
        )


def _call_groq_vision(
    image_path: str
) -> str:

    if not groq_client:

        raise RuntimeError(
            "Groq vision client unavailable."
        )


    if not GROQ_VISION_MODEL:

        raise RuntimeError(
            "Groq vision model unavailable."
        )


    base64_image = (
        encode_image(
            image_path
        )
    )


    mime_type = (
        mimetypes.guess_type(
            image_path
        )[0]
        or
        "image/jpeg"
    )


    response = (
        groq_client
        .chat
        .completions
        .create(
            model=GROQ_VISION_MODEL,

            messages=[
                {
                    "role":
                        "user",

                    "content": [
                        {
                            "type":
                                "text",

                            "text":
                                VISION_PROMPT
                        },

                        {
                            "type":
                                "image_url",

                            "image_url": {
                                "url":
                                    (
                                        f"data:"
                                        f"{mime_type};"
                                        f"base64,"
                                        f"{base64_image}"
                                    )
                            }
                        }
                    ]
                }
            ],

            temperature=0.1
        )
    )


    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


def _call_gemini_vision(
    image_path: str
) -> str:

    if not gemini_client:

        raise RuntimeError(
            "Gemini vision client unavailable."
        )


    mime_type = (
        mimetypes.guess_type(
            image_path
        )[0]
        or
        "image/jpeg"
    )


    with open(
        image_path,
        "rb"
    ) as file:

        image_bytes = (
            file.read()
        )


    # Shared with text_llm.py.
    # Text and vision therefore respect one
    # Gemini request-rate budget.
    wait_for_gemini_slot()


    image_part = (
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type
        )
    )


    response = (
        gemini_client
        .models
        .generate_content(
            model=GEMINI_VISION_MODEL,

            contents=[
                VISION_PROMPT,
                image_part
            ]
        )
    )


    return (
        response.text.strip()
        if response.text
        else ""
    )


def describe_educational_image(
    image_path: str
) -> str:

    # =====================================================
    # Provider 1 — Groq
    # =====================================================

    if groq_client:

        try:

            description = (
                _call_groq_vision(
                    image_path
                )
            )


            print(
                "[Vision LLM] "
                "Provider: Groq"
            )


            return description


        except RateLimitError:

            print(
                "[Vision LLM] "
                "Groq rate limit reached."
            )

            print(
                "[Vision LLM] "
                "Falling back to Gemini..."
            )


        except Exception as exc:

            print(
                "[Vision LLM] "
                f"Groq failed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print(
                "[Vision LLM] "
                "Trying Gemini..."
            )


    # =====================================================
    # Provider 2 — Gemini
    # =====================================================

    if gemini_client:

        try:

            description = (
                _call_gemini_vision(
                    image_path
                )
            )


            print(
                "[Vision LLM] "
                "Provider: Gemini"
            )


            return description


        except Exception as exc:

            retry_after = (
                get_retry_after_seconds(
                    exc
                )
            )


            print(
                "[Vision LLM] "
                f"Gemini failed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )


            raise LLMUnavailableError(
                (
                    "All configured vision "
                    "providers are unavailable."
                ),
                retry_after_seconds=(
                    retry_after
                )
            ) from exc


    raise LLMUnavailableError(
        "No vision LLM provider is available."
    )