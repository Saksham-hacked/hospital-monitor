"""
Shared Gemini call wrapper with structured logging and retry logic.
All LLM calls in this project go through gemini_call() so every
request/response is traceable in one place.
"""

import logging
import time
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

logger = logging.getLogger("gemini")

# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]  # seconds between attempts


def gemini_call(
    prompt: str,
    model: str = "gemini-2.5-flash",
    caller: str = "unknown",
) -> str:
    """
    Make a Gemini API call with structured logging and retry.

    Args:
        prompt:  The full prompt string to send.
        model:   Model name to use.
        caller:  Label for logs (e.g. "normalizer", "trend_summarizer").

    Returns:
        Response text string.

    Raises:
        Exception if all retries are exhausted.
    """
    prompt_preview = prompt[:120].replace("\n", " ")

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(
            "[Gemini] call | caller=%s model=%s attempt=%d/%d prompt_preview='%s...'",
            caller, model, attempt, MAX_RETRIES, prompt_preview,
        )
        t0 = time.monotonic()
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            elapsed = time.monotonic() - t0
            text = response.text.strip()
            logger.info(
                "[Gemini] ok    | caller=%s attempt=%d elapsed=%.2fs chars=%d",
                caller, attempt, elapsed, len(text),
            )
            return text

        except Exception as e:
            elapsed = time.monotonic() - t0
            logger.warning(
                "[Gemini] error | caller=%s attempt=%d elapsed=%.2fs error=%s",
                caller, attempt, elapsed, e,
            )
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[attempt - 1]
                logger.info("[Gemini] retry | caller=%s waiting %ds...", caller, wait)
                time.sleep(wait)
            else:
                logger.error(
                    "[Gemini] failed | caller=%s all %d attempts exhausted.",
                    caller, MAX_RETRIES,
                )
                raise
