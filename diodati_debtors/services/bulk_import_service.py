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
import io

import pandas as pd
from .book_service import create_book, generate_summary_with_ai

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
    existing_book_id: int | None  # None when matched against another row in this file, not a saved book
    existing_book_title: str
    match_reason: str  # "isbn" | "title_author"
    duplicate_of_row_index: int | None = None  # set when the match is an earlier row in the same upload

    def to_dict(self) -> dict:
        return asdict(self)
    
def _clean_isbn(raw_value: str | None) -> str | None:
    """Strips the Excel formula wrapper some exporters (notably
    Goodreads) use to preserve leading zeros, e.g. ="0141439793" — a
    real edge case discovered while testing with an authentic
    Goodreads-shaped export, not a hypothetical one.
    """
    if not raw_value:
        return None
    cleaned = raw_value.strip()
    if cleaned.startswith('="') and cleaned.endswith('"'):
        cleaned = cleaned[2:-1]
    return cleaned.strip() or None


def find_duplicates(
    owner_id: int, rows: list[dict], mapping: dict[str, "ColumnMatch | None"]
) -> list[DuplicateCandidate]:
    """Checks each row against (1) the owner's existing books, and (2)
    earlier rows within the same uploaded file — a spreadsheet can
    itself contain accidental repeat entries (discovered via a real
    test file containing two identical "Hobbit" rows in one upload).
    ISBN match takes priority over title+author match, per the Domain
    Model. Never merges automatically — every candidate is surfaced
    for the user to decide (default: skip).
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
        seen_rows: list[tuple[int, str, str | None, str | None]] = []

        for index, row in enumerate(rows):
            row_title = (row.get(title_header) or "").strip()
            row_author = (row.get(author_header) or "").strip() if author_header else None
            row_isbn = _clean_isbn(row.get(isbn_header)) if isbn_header else None

            if not row_title:
                continue

            matched_book_id = None
            matched_title = None
            matched_row_index = None
            reason = None

            if row_isbn:
                for book in existing_books:
                    if book.isbn and book.isbn.strip() == row_isbn:
                        matched_book_id = book.id
                        matched_title = book.title
                        reason = "isbn"
                        break

            if matched_book_id is None and row_author:
                for book in existing_books:
                    if (
                        book.title.strip().lower() == row_title.lower()
                        and book.author
                        and book.author.strip().lower() == row_author.lower()
                    ):
                        matched_book_id = book.id
                        matched_title = book.title
                        reason = "title_author"
                        break

            if matched_book_id is None:
                if row_isbn:
                    for seen_index, seen_title, _, seen_isbn in seen_rows:
                        if seen_isbn and seen_isbn == row_isbn:
                            matched_row_index = seen_index
                            matched_title = seen_title
                            reason = "isbn"
                            break

                if matched_row_index is None and row_author:
                    for seen_index, seen_title, seen_author, _ in seen_rows:
                        if (
                            seen_title.lower() == row_title.lower()
                            and seen_author
                            and seen_author.lower() == row_author.lower()
                        ):
                            matched_row_index = seen_index
                            matched_title = seen_title
                            reason = "title_author"
                            break

            if matched_book_id is not None or matched_row_index is not None:
                candidates.append(
                    DuplicateCandidate(
                        row_index=index,
                        row_title=row_title,
                        row_author=row_author,
                        row_isbn=row_isbn,
                        existing_book_id=matched_book_id,
                        existing_book_title=matched_title or "",
                        match_reason=reason,
                        duplicate_of_row_index=matched_row_index,
                    )
                )

            seen_rows.append((index, row_title, row_author, row_isbn))

        return candidates
def _read_csv_with_encoding_fallback(content: bytes) -> pd.DataFrame:
    """Tries known encodings crossed with known delimiters,
    deterministically. For each combination, tries a strict parse
    first; if that fails due to malformed rows (a real issue in
    large, user-submitted datasets like Book-Crossing, which contains
    genuinely broken quote-escaping in some rows), retries the same
    combination while skipping unparseable lines rather than
    abandoning the whole file.
    """
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        for delimiter in (";", ",", "\t", "|"):
            for on_bad_lines in ("error", "skip"):
                try:
                    df = pd.read_csv(
                        io.BytesIO(content),
                        sep=delimiter,
                        engine="python",
                        encoding=encoding,
                        on_bad_lines=on_bad_lines,
                    )
                except (UnicodeDecodeError, pd.errors.ParserError, ValueError):
                    continue
                if len(df.columns) > 1:
                    return df
    raise ValueError("Could not determine the file's text encoding or delimiter.")
    
def parse_uploaded_file(filename: str, content: bytes) -> tuple[list[str], list[dict]]:
    """Reads CSV, XLSX, or ODS into a neutral (headers, rows) shape —
    a single entry point regardless of format, per the Domain Model's
    "File Reader" responsibility. Engine choice is automatic based on
    file extension; pandas + openpyxl/odfpy handle the format
    differences internally.

    Raises ValueError for unsupported extensions or unreadable files —
    not a DiodatiError, since this is closer to input validation than
    a business rule (consistent with how ISBN lookup failures are
    handled elsewhere).
    """
    lower_name = filename.lower()

    try:
        if lower_name.endswith(".csv"):
            df = _read_csv_with_encoding_fallback(content)
        elif lower_name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        elif lower_name.endswith(".ods"):
            df = pd.read_excel(io.BytesIO(content), engine="odf")
        else:
            raise ValueError(
                f"Unsupported file type: {filename}. Please upload a "
                f".csv, .xlsx, or .ods file."
            )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not read the file: {e}") from e

    df = df.fillna("")
    headers = [str(col) for col in df.columns]
    rows = df.astype(str).to_dict(orient="records")
    return headers, rows


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

@dataclass(frozen=True)
class SkippedRow:
    row_index: int
    reason: str  # "missing_title" | "duplicate_skipped" | "creation_failed"
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ImportReport:
    total_rows: int
    imported_count: int
    skipped: list[SkippedRow]

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "imported_count": self.imported_count,
            "skipped": [s.to_dict() for s in self.skipped],
        }

def import_books(
    owner_id: int,
    rows: list[dict],
    mapping: dict[str, ColumnMatch | None],
    skip_row_indices: set[int],
    generate_ai_summaries: bool = False,
) -> ImportReport:
    """Creates Book rows from parsed import data. Never aborts the
    whole batch over individual bad rows — every failure is recorded
    in the report, not raised, per the Domain Model's "robust rather
    than strict" principle. skip_row_indices are rows the user
    explicitly chose to skip as duplicates.
    """
    title_header = mapping["title"].header if mapping.get("title") else None
    author_header = mapping["author"].header if mapping.get("author") else None
    isbn_header = mapping["isbn"].header if mapping.get("isbn") else None

    skipped: list[SkippedRow] = []
    imported_count = 0

    for index, row in enumerate(rows):
        if index in skip_row_indices:
            skipped.append(
                SkippedRow(row_index=index, reason="duplicate_skipped", detail="Matched an existing book.")
            )
            continue

        row_title = (row.get(title_header) or "").strip() if title_header else ""
        if not row_title:
            skipped.append(
                SkippedRow(row_index=index, reason="missing_title", detail="No title found in this row.")
            )
            continue

        row_author = (row.get(author_header) or "").strip() or None if author_header else None
        row_isbn = _clean_isbn(row.get(isbn_header)) if isbn_header else None

        try:
            book = create_book(
                owner_id=owner_id, title=row_title, author=row_author, isbn=row_isbn
            )
        except Exception as e:
            skipped.append(SkippedRow(row_index=index, reason="creation_failed", detail=str(e)))
            continue

        imported_count += 1

        if generate_ai_summaries:
            try:
                generate_summary_with_ai(book.id, owner_id=owner_id)
            except Exception:
                pass  # best-effort enrichment, never breaks the import itself

    return ImportReport(total_rows=len(rows), imported_count=imported_count, skipped=skipped)


__all__ = [
    "ColumnMatch",
    "DuplicateCandidate",
    "SkippedRow",
    "ImportReport",
    "detect_column_mapping",
    "is_high_confidence_mapping",
    "find_duplicates",
    "parse_uploaded_file",
    "import_books",
]