"""Raw HTTP client for the Open Library Books API.

Endpoint verified (project vault, Domain Model v2 research):
GET {base_url}/api/books?bibkeys=ISBN:xxxx&format=json&jscmd=data
Returns {"ISBN:xxxx": {...}} if found, or {} if the ISBN has no match
— absence of the key means "not found", not an HTTP error.

This module is deliberately thin: parsing/business meaning (what does
"not found" mean for us, what fields do we actually use) lives in
book_service.lookup_isbn(), not here. This file only knows how to talk
to the API.
"""

from __future__ import annotations

import requests

from ...core.config import settings

_TIMEOUT_SECONDS = 5
_USER_AGENT = "TheDiodatiDebtors (contact: local-dev)"


def fetch_book_by_isbn(isbn: str) -> dict | None:
    """Fetch raw Open Library data for one ISBN.

    Returns the book's data dict, or None if Open Library has no
    record for this ISBN. Network/timeout errors propagate as
    requests.RequestException (or a subclass) — not translated into a
    domain exception here.
    """
    bib_key = f"ISBN:{isbn}"
    response = requests.get(
        f"{settings.open_library_base_url}/api/books",
        params={"bibkeys": bib_key, "format": "json", "jscmd": "data"},
        headers={"User-Agent": _USER_AGENT},
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data.get(bib_key)


__all__ = ["fetch_book_by_isbn"]