"""Raw HTTP client for the Open Library Search API — a different
endpoint and response shape than the Books API (open_library_client.py).

GET {base_url}/search.json?q=...&limit=...&fields=...
Returns {"numFound": N, "docs": [{...}, {...}, ...]}, a list of
possible matches (editions/translations/revisions may all appear
separately) — never a single resolved book.

This module is deliberately thin: parsing/business meaning lives in
book_service.search_books(), not here.
"""

from __future__ import annotations

import requests

from ...core.config import settings

_TIMEOUT_SECONDS = 5
_USER_AGENT = "TheDiodatiDebtors (contact: local-dev)"
_FIELDS = "key,title,author_name,first_publish_year,cover_i,isbn,edition_count"


def search_books_raw(query: str, limit: int = 20) -> list[dict]:
    """Fetch raw Open Library search results for a free-text query.

    Returns the "docs" list as-is (each item is one possible match).
    Empty list means genuinely no results — not an error. Network/
    timeout errors propagate as requests.RequestException.
    """
    response = requests.get(
        f"{settings.open_library_base_url}/search.json",
        params={"q": query, "limit": limit, "fields": _FIELDS},
        headers={"User-Agent": _USER_AGENT},
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("docs", [])


__all__ = ["search_books_raw"]