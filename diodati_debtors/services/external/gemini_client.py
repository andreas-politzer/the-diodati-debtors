"""Thin HTTP client for the Gemini API (generateContent endpoint).
No business logic here — prompt construction and error meaning live
in book_service, not here.
"""

from __future__ import annotations

import requests

from ...core.config import settings

_TIMEOUT_SECONDS = 15


def generate_text(prompt: str) -> str:
    """Send a single-turn prompt, return the model's text response.

    Raises requests.RequestException on network/HTTP failure, or
    ValueError if the response has no usable text (e.g. blocked by
    safety filters) — neither is translated into a domain exception
    here, per the Service Contract.
    """
    url = f"{settings.gemini_base_url}/models/{settings.gemini_model}:generateContent"
    response = requests.post(
        url,
        headers={
            "x-goog-api-key": settings.gemini_api_key,
            "Content-Type": "application/json",
        },
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise ValueError("Gemini response contained no usable text.") from e


__all__ = ["generate_text"]