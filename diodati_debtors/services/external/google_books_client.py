"""Thin HTTP client for the Google Books API — searches by free-text
query (used for the Librarian's fallback, searching the user's
original question rather than a Gemini-generated title). No business
logic here, per the Service Contract.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from ...core.config import settings

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
    error state, consistent with how Open Library's search behaves
    elsewhere in this project.
    """
    try:
        response = requests.get(
            _BASE_URL,
            params={
                "q": query,
                "maxResults": max_results,
                "key": settings.google_books_api_key,
            },
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    results = []
    for item in data.get("items", []):
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