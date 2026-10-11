import json
import os
import re
import threading
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

    def __init__(
        self,
        message: str,
        retry_after_seconds: float | None = None
    ):
        super().__init__(message)

        self.retry_after_seconds = (
            retry_after_seconds
        )


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
    "gemini-3.8-flash"
)


# Gemini free tier currently has a very small
# requests-per-minute allowance.
#
# 13 seconds ≈ 4.6 requests/minute.
GEMINI_MIN_INTERVAL_SECONDS = float(
    os.getenv(
        "GEMINI_MIN_INTERVAL_SECONDS",
        "13"
    )
)


# Do not freeze an HTTP request for a minute if
# Gemini tells us to retry in ~59 seconds.
GEMINI_MAX_RETRY_WAIT_SECONDS = float(
    os.getenv(
        "GEMINI_MAX_RETRY_WAIT_SECONDS",
        "15"
    )
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
# Shared Gemini request throttle
# =====================================================

_gemini_lock = threading.Lock()

_gemini_last_request_time = 0.0


def wait_for_gemini_slot():
    """
    Global Gemini throttle.

    Both text and image calls can use this function,
    preventing them from independently exceeding
    the same Gemini project RPM quota.
    """

    global _gemini_last_request_time

    with _gemini_lock:

        now = time.monotonic()

        elapsed = (
            now
            - _gemini_last_request_time
        )

        wait_time = (
            GEMINI_MIN_INTERVAL_SECONDS
            - elapsed
        )


        if wait_time > 0:

            print(
                "[Gemini Throttle] "
                f"Waiting {wait_time:.1f}s..."
            )

            time.sleep(
                wait_time
            )


        _gemini_last_request_time = (
            time.monotonic()
        )


# =====================================================
# Retry delay parser
# =====================================================

def get_retry_after_seconds(
    exc: Exception
) -> float | None:

    message = str(
        exc
    )


    patterns = [
        r"retryDelay['\"]?\s*:\s*['\"]?([\d.]+)s",
        r"retry in ([\d.]+)s",
        r"retry after ([\d.]+)s"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            message,
            flags=re.IGNORECASE
        )


        if match:

            try:

                return float(
                    match.group(1)
                )

            except ValueError:

                pass


    return None


# =====================================================
# JSON helper
# =====================================================

def _clean_json_response(
    raw_content: str
) -> dict:

    if not raw_content:
        return {}


    raw_content = (
        raw_content.strip()
    )


    if raw_content.startswith(
        "```"
    ):

        raw_content = (
            raw_content
            .replace(
                "```json",
                ""
            )
            .replace(
                "```JSON",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )


    try:

        return json.loads(
            raw_content
        )


    except json.JSONDecodeError:

        print(
            "[Text LLM] "
            "Invalid JSON response:"
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


    if not GROQ_MODEL:

        raise RuntimeError(
            "Groq model is not configured."
        )


    response = (
        groq_client
        .chat
        .completions
        .create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role":
                        "system",

                    "content":
                        system_prompt
                },
                {
                    "role":
                        "user",

                    "content":
                        prompt
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
        or ""
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


    wait_for_gemini_slot()


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
# Gemini error detection
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
# Gemini retry
# =====================================================

def _call_gemini_with_retry(
    prompt: str,
    system_prompt: str,
    max_attempts: int = 3
) -> dict:

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
                "[Text LLM] "
                "Provider: Gemini"
            )


            return result


        except Exception as exc:

            last_exception = exc


            print(
                f"[Text LLM] "
                f"Gemini attempt "
                f"{attempt}/{max_attempts} "
                f"failed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )


            if not _is_retryable_gemini_error(
                exc
            ):

                break


            retry_after = (
                get_retry_after_seconds(
                    exc
                )
            )


            # ---------------------------------------------
            # Provider says wait too long.
            #
            # Do NOT hammer it repeatedly.
            # Let checkpoint/resume architecture handle it.
            # ---------------------------------------------

            if (
                retry_after is not None
                and
                retry_after
                > GEMINI_MAX_RETRY_WAIT_SECONDS
            ):

                print(
                    "[Text LLM] "
                    f"Gemini requested a "
                    f"{retry_after:.1f}s retry delay."
                )

                print(
                    "[Text LLM] "
                    "Deferring instead of "
                    "blocking the request."
                )


                raise LLMUnavailableError(
                    (
                        "Gemini rate limit window "
                        "has not reset yet."
                    ),
                    retry_after_seconds=(
                        retry_after
                    )
                ) from exc


            if attempt >= max_attempts:
                break


            if retry_after is not None:

                delay = max(
                    retry_after,
                    1.0
                )

            else:

                delay = min(
                    2 ** attempt,
                    8
                )


            print(
                "[Text LLM] "
                f"Retrying Gemini in "
                f"{delay:.1f}s..."
            )


            time.sleep(
                delay
            )


    raise LLMUnavailableError(
        "Gemini remained unavailable after retries.",
        retry_after_seconds=(
            get_retry_after_seconds(
                last_exception
            )
            if last_exception
            else None
        )
    ) from last_exception


# =====================================================
# Public router
# =====================================================

def generate_json(
    prompt: str,
    system_prompt: str
) -> dict:

    groq_failed = False


    # =================================================
    # Provider 1 — Groq
    # =================================================

    if groq_client:

        try:

            result = _call_groq(
                prompt=prompt,
                system_prompt=system_prompt
            )


            print(
                "[Text LLM] "
                "Provider: Groq"
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


    # =================================================
    # Provider 2 — Gemini
    # =================================================

    if gemini_client:

        return _call_gemini_with_retry(
            prompt=prompt,
            system_prompt=system_prompt
        )


    # =================================================
    # Nothing worked
    # =================================================

    if groq_failed:

        raise LLMUnavailableError(
            (
                "Groq failed and no working "
                "fallback provider is available."
            )
        )


    raise LLMUnavailableError(
        "No text LLM provider is currently available."
    )