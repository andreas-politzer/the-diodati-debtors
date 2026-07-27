"""Bulk Import service — CSV/XLSX/ODS upload for existing personal
libraries (see Bulk Import Domain Model, project vault). No new
database table: imported books become ordinary Book rows via the
existing book_service.create_book.

Column Detector is the first, independent building block: pure
mapping logic, no file I/O, no database — deterministic and easy to
unit test in isolation (per ChatGPT's review).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

_SYNONYMS: dict[str, list[str]] = {
    "title": ["title", "book title", "buchtitel", "titel", "name"],
    "author": ["author", "autor", "writer", "verfasser"],
    "isbn": ["isbn", "isbn-13", "isbn13", "isbn-10", "isbn10", "ean"],
}


@dataclass(frozen=True)
class ColumnMatch:
    field: str  # "title" | "author" | "isbn"
    header: str  # the actual column header from the file
    confidence: str  # "high" | "low"

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize(header: str) -> str:
    return header.strip().lower().replace("_", " ").replace("-", " ")


def detect_column_mapping(headers: list[str]) -> dict[str, ColumnMatch | None]:
    """For each target field (title/author/isbn), find the best
    matching header. High confidence = exact match after
    normalization. Low confidence = the normalized header contains a
    synonym as a substring (e.g. "Book Title (English)" contains
    "title"). None if no header matches at all — the field stays
    "Unused" in the review UI, per ChatGPT's suggestion to never
    silently discard unrecognized columns.
    """
    normalized_headers = {header: _normalize(header) for header in headers}
    result: dict[str, ColumnMatch | None] = {}

    for field, synonyms in _SYNONYMS.items():
        match: ColumnMatch | None = None

        # Pass 1: exact match after normalization.
        for header, normalized in normalized_headers.items():
            if normalized in synonyms:
                match = ColumnMatch(field=field, header=header, confidence="high")
                break

        # Pass 2: substring containment, only if no exact match found.
        if match is None:
            for header, normalized in normalized_headers.items():
                if any(syn in normalized for syn in synonyms):
                    match = ColumnMatch(field=field, header=header, confidence="low")
                    break

        result[field] = match

    return result


def is_high_confidence_mapping(mapping: dict[str, ColumnMatch | None]) -> bool:
    """Progressive disclosure gate: only the Title field must be
    high-confidence for the one-line confirmation to appear (Author/
    ISBN are optional metadata, not required for a usable import).
    Anything else routes to the detailed mapping table.
    """
    title_match = mapping.get("title")
    return title_match is not None and title_match.confidence == "high"


__all__ = ["ColumnMatch", "detect_column_mapping", "is_high_confidence_mapping"]