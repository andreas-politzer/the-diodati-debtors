"""Tests for google_books_client.search_books — mocked HTTP responses,
no real API calls. Errors return an empty list, never raise — "no
result" and "request failed" look the same to callers, per the
client's own documented behavior.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from diodati_debtors.services.external import google_books_client


def test_search_books_returns_parsed_results():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "items": [
            {
                "volumeInfo": {
                    "title": "Frankenstein",
                    "authors": ["Mary Shelley"],
                    "industryIdentifiers": [
                        {"type": "ISBN_13", "identifier": "9780141439471"},
                    ],
                    "imageLinks": {"thumbnail": "https://example.com/cover.jpg"},
                    "infoLink": "https://books.google.com/books?id=abc123",
                }
            }
        ]
    }

    with patch(
        "diodati_debtors.services.external.google_books_client.requests.get",
        return_value=mock_response,
    ):
        results = google_books_client.search_books("Frankenstein")

    assert len(results) == 1
    assert results[0].title == "Frankenstein"
    assert results[0].author == "Mary Shelley"
    assert results[0].isbn == "9780141439471"
    assert results[0].cover_url == "https://example.com/cover.jpg"


def test_search_books_returns_empty_list_when_no_items():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}

    with patch(
        "diodati_debtors.services.external.google_books_client.requests.get",
        return_value=mock_response,
    ):
        results = google_books_client.search_books("something obscure")

    assert results == []


def test_search_books_returns_empty_list_on_request_exception():
    with patch(
        "diodati_debtors.services.external.google_books_client.requests.get",
        side_effect=requests.RequestException("simulated network failure"),
    ):
        results = google_books_client.search_books("anything")

    assert results == []


def test_search_books_handles_missing_author_and_isbn():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "items": [{"volumeInfo": {"title": "Mystery Book"}}]
    }

    with patch(
        "diodati_debtors.services.external.google_books_client.requests.get",
        return_value=mock_response,
    ):
        results = google_books_client.search_books("mystery")

    assert results[0].title == "Mystery Book"
    assert results[0].author is None
    assert results[0].isbn is None