import os
import json
import time

from dotenv import load_dotenv

from groq import (
    Groq,
    RateLimitError
)

from google import genai


load_dotenv()


# =====================================================
# Custom exception
# =====================================================

class LLMUnavailableError(RuntimeError):
    """
    Raised only when every configured LLM provider
    is temporarily unavailable or fails.
    """

    pass


# =====================================================
# Configuration
# =====================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_MODEL = os.getenv(
    "model"
)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_TEXT_MODEL",
    "gemini-2.5-flash"
)


# =====================================================
# Clients
# =====================================================

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


# =====================================================
# JSON helper
# =====================================================

def _clean_json_response(
    raw_content: str
) -> dict:

    if not raw_content:
        return {}


    raw_content = raw_content.strip()


    if raw_content.startswith("```"):

        raw_content = (
            raw_content
            .replace("```json", "")
            .replace("```JSON", "")
            .replace("```", "")
            .strip()
        )


    try:

        return json.loads(
            raw_content
        )


    except json.JSONDecodeError:

        print(
            "[Text LLM] Invalid JSON response:"
        )

        print(
            raw_content
        )

        return {}


# =====================================================
# Groq
# =====================================================

def _call_groq(
    prompt: str,
    system_prompt: str
) -> dict:

    if not groq_client:

        raise RuntimeError(
            "Groq client is unavailable."
        )


    response = (
        groq_client
        .chat
        .completions
        .create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.0
        )
    )


    raw_content = (
        response
        .choices[0]
        .message
        .content
    )


    return _clean_json_response(
        raw_content
    )


# =====================================================
# Gemini
# =====================================================

def _call_gemini(
    prompt: str,
    system_prompt: str
) -> dict:

    if not gemini_client:

        raise RuntimeError(
            "Gemini client is unavailable."
        )


    full_prompt = f"""
SYSTEM INSTRUCTIONS:

{system_prompt}


USER REQUEST:

{prompt}
"""


    response = (
        gemini_client
        .models
        .generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt
        )
    )


    raw_content = (
        response.text
        if response.text
        else ""
    )


    return _clean_json_response(
        raw_content
    )


# =====================================================
# Detect retryable Gemini errors
# =====================================================

def _is_retryable_gemini_error(
    exc: Exception
) -> bool:

    message = str(
        exc
    ).lower()


    retryable_patterns = [
        "503",
        "unavailable",
        "high demand",
        "temporarily unavailable",
        "429",
        "resource_exhausted",
        "rate limit"
    ]


    return any(
        pattern in message
        for pattern in retryable_patterns
    )


# =====================================================
# Gemini with retries
# =====================================================

def _call_gemini_with_retry(
    prompt: str,
    system_prompt: str,
    max_attempts: int = 3
) -> dict:

    delays = [
        2,
        4,
        8
    ]


    last_exception = None


    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            result = _call_gemini(
                prompt=prompt,
                system_prompt=system_prompt
            )


            print(
                "[Text LLM] Provider: Gemini"
            )


            return result


        except Exception as exc:

            last_exception = exc


            retryable = (
                _is_retryable_gemini_error(
                    exc
                )
            )


            print(
                f"[Text LLM] Gemini attempt "
                f"{attempt}/{max_attempts} failed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )


            if not retryable:

                break


            if attempt >= max_attempts:

                break


            delay = delays[
                min(
                    attempt - 1,
                    len(delays) - 1
                )
            ]


            print(
                f"[Text LLM] "
                f"Retrying Gemini in "
                f"{delay} seconds..."
            )


            time.sleep(
                delay
            )


    raise LLMUnavailableError(
        "Gemini remained unavailable after retries."
    ) from last_exception


# =====================================================
# Public provider router
# =====================================================

def generate_json(
    prompt: str,
    system_prompt: str
) -> dict:

    groq_failed = False


    # -------------------------------------------------
    # Provider 1 — Groq
    # -------------------------------------------------

    if groq_client:

        try:

            result = _call_groq(
                prompt=prompt,
                system_prompt=system_prompt
            )


            print(
                "[Text LLM] Provider: Groq"
            )


            return result


        except RateLimitError:

            groq_failed = True


            print(
                "[Text LLM] "
                "Groq rate limit reached."
            )

            print(
                "[Text LLM] "
                "Falling back to Gemini..."
            )


        except Exception as exc:

            groq_failed = True


            print(
                "[Text LLM] "
                f"Groq failed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print(
                "[Text LLM] "
                "Trying Gemini..."
            )


    # -------------------------------------------------
    # Provider 2 — Gemini
    # -------------------------------------------------

    if gemini_client:

        try:

            return _call_gemini_with_retry(
                prompt=prompt,
                system_prompt=system_prompt
            )


        except LLMUnavailableError:

            raise


        except Exception as exc:

            raise LLMUnavailableError(
                "Gemini provider failed."
            ) from exc


    # -------------------------------------------------
    # Nothing worked
    # -------------------------------------------------

    if groq_failed:

        raise LLMUnavailableError(
            "Groq failed and no working fallback "
            "provider is available."
        )


    raise LLMUnavailableError(
        "No text LLM provider is currently available."
    )