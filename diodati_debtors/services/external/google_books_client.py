"""Thin HTTP client for the Google Books API — searches by free-text
query (used for the Librarian's fallback, searching the user's
original question rather than a Gemini-generated title). No business
logic here, per the Service Contract.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from ...core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10
_BASE_URL = "https://www.googleapis.com/books/v1/volumes"


@dataclass(frozen=True)
class GoogleBookResult:
    title: str
    author: str | None
    isbn: str | None
    cover_url: str | None
    info_link: str | None


def search_books(query: str, max_results: int = 5) -> list[GoogleBookResult]:
    """Searches Google Books by free-text query. Returns an empty list
    (not an exception) if nothing is found or the request fails —
    callers treat "no results" as a normal, expected outcome, not an
    error state. Failures ARE logged, per the 28.07 "silent failure"
    investigation. Retries once on a 503 (transient server overload),
    per the same investigation — Google Books returned a genuine 503
    during testing, unrelated to our own code.
    """
    for attempt in range(2):
        logger.info("GoogleBooks: query=%r max_results=%d attempt=%d", query, max_results, attempt + 1)
        try:
            response = requests.get(
                _BASE_URL,
                params={
                    "q": query,
                    "maxResults": max_results,
                    "key": settings.google_books_api_key,
                },
                timeout=(3.0, _TIMEOUT_SECONDS),
            )
            logger.info("GoogleBooks: response status=%d for query=%r", response.status_code, query)
            response.raise_for_status()
            data = response.json()
            break
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 503 and attempt == 0:
                logger.warning("GoogleBooks: 503, retrying once for query=%r", query)
                continue
            logger.error("GoogleBooks: request failed for query=%r: %s", query, e, exc_info=True)
            return []
        except requests.RequestException as e:
            logger.error("GoogleBooks: request failed for query=%r: %s", query, e, exc_info=True)
            return []
        except ValueError:
            logger.error("GoogleBooks: could not parse JSON response for query=%r", query, exc_info=True)
            return []
    else:
        return []

    items = data.get("items", [])
    logger.info("GoogleBooks: %d items returned for query=%r", len(items), query)

    results = []
    for item in items:
        info = item.get("volumeInfo", {})
        identifiers = info.get("industryIdentifiers", [])
        isbn = next(
            (i["identifier"] for i in identifiers if i.get("type") == "ISBN_13"),
            None,
        )
        image_links = info.get("imageLinks", {})
        results.append(
            GoogleBookResult(
                title=info.get("title", "Unknown title"),
                author=", ".join(info.get("authors", [])) or None,
                isbn=isbn,
                cover_url=image_links.get("thumbnail"),
                info_link=info.get("infoLink"),
            )
        )
    return results


__all__ = ["GoogleBookResult", "search_books"]