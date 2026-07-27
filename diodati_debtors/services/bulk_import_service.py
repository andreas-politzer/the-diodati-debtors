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
from sqlalchemy import select

from ..db.session import get_session
from ..models.book import Book

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
    
@dataclass(frozen=True)
class DuplicateCandidate:
    row_index: int
    row_title: str
    row_author: str | None
    row_isbn: str | None
    existing_book_id: int
    existing_book_title: str
    match_reason: str  # "isbn" | "title_author"

    def to_dict(self) -> dict:
        return asdict(self)


def find_duplicates(
    owner_id: int, rows: list[dict], mapping: dict[str, "ColumnMatch | None"]
) -> list[DuplicateCandidate]:
    """Checks each row against the owner's existing books. ISBN match
    takes priority over title+author match, per the Domain Model.
    Never merges automatically — every candidate is surfaced for the
    user to decide (default: skip).
    """
    title_header = mapping["title"].header if mapping.get("title") else None
    author_header = mapping["author"].header if mapping.get("author") else None
    isbn_header = mapping["isbn"].header if mapping.get("isbn") else None

    if title_header is None:
        return []

    with get_session() as session:
        existing_books = session.scalars(
            select(Book).where(Book.owner_id == owner_id)
        ).all()

        candidates: list[DuplicateCandidate] = []
        for index, row in enumerate(rows):
            row_title = (row.get(title_header) or "").strip()
            row_author = (row.get(author_header) or "").strip() if author_header else None
            row_isbn = (row.get(isbn_header) or "").strip() if isbn_header else None

            if not row_title:
                continue

            matched_book = None
            reason = None

            if row_isbn:
                for book in existing_books:
                    if book.isbn and book.isbn.strip() == row_isbn:
                        matched_book = book
                        reason = "isbn"
                        break

            if matched_book is None and row_author:
                for book in existing_books:
                    if (
                        book.title.strip().lower() == row_title.lower()
                        and book.author
                        and book.author.strip().lower() == row_author.lower()
                    ):
                        matched_book = book
                        reason = "title_author"
                        break

            if matched_book is not None:
                candidates.append(
                    DuplicateCandidate(
                        row_index=index,
                        row_title=row_title,
                        row_author=row_author,
                        row_isbn=row_isbn,
                        existing_book_id=matched_book.id,
                        existing_book_title=matched_book.title,
                        match_reason=reason,
                    )
                )

        return candidates


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


__all__ = ["ColumnMatch", "detect_column_mapping", "is_high_confidence_mapping", "DuplicateCandidate", "find_duplicates",]