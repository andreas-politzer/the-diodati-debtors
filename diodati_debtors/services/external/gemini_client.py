"""Thin HTTP client for the Gemini API (generateContent endpoint).
No business logic here — prompt construction and error meaning live
in book_service, not here.
"""

from __future__ import annotations

import requests

from ...core.config import settings

_TIMEOUT_SECONDS = 20


def generate_text(prompt: str) -> str:
    """Send a single-turn prompt, return the model's text response.
    Retries once on a transient network/timeout failure — per the
    29.07 investigation, Gemini occasionally times out even within a
    generous window, and the Librarian's remark call failing silently
    was masking real Byron responses behind a generic fallback string.

    Raises requests.RequestException on network/HTTP failure (after
    the retry), or ValueError if the response has no usable text
    (e.g. blocked by safety filters) — neither is translated into a
    domain exception here, per the Service Contract.
    """
    url = f"{settings.gemini_base_url}/models/{settings.gemini_model}:generateContent"
    last_error = None
    for attempt in range(2):
        try:
            response = requests.post(
                url,
                headers={
                    "x-goog-api-key": settings.gemini_api_key,
                    "Content-Type": "application/json",
                },
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=(3.0, _TIMEOUT_SECONDS),
            )
            response.raise_for_status()
            data = response.json()
            break
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            if attempt == 0:
                continue
            raise
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (500, 502, 503, 504) and attempt == 0:
                last_error = e
                continue
            raise
    else:
        raise last_error

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise ValueError("Gemini response contained no usable text.") from e
    
def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """Convert text into an embedding vector via Gemini's embedContent
    endpoint. task_type matters for retrieval quality — use
    RETRIEVAL_DOCUMENT when embedding a book's own text (indexing),
    RETRIEVAL_QUERY when embedding a user's search phrase (see Google's
    own guidance for retrieval scenarios).

    Raises requests.RequestException on network/HTTP failure, or
    ValueError if the response has no usable embedding — neither is
    translated into a domain exception here, per the Service Contract.
    """
    url = f"{settings.gemini_base_url}/models/{settings.gemini_embedding_model}:embedContent"
    response = requests.post(
        url,
        headers={
            "x-goog-api-key": settings.gemini_api_key,
            "Content-Type": "application/json",
        },
        json={
            "content": {"parts": [{"text": text}]},
            "task_type": task_type,
            "output_dimensionality": 768,
        },
        timeout=(3.0, _TIMEOUT_SECONDS),
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["embedding"]["values"]
    except KeyError as e:
        raise ValueError("Gemini response contained no usable embedding.") from e


__all__ = ["generate_text", "embed_text"]