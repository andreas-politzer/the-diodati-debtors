"""Book service. Per the Service Contract (Implementation
Specification.md): plain inputs, dataclass return values, domain
exceptions, self-contained transactions, no Reflex import.

Open Library ISBN lookup is deferred — isbn here is accepted only as a
plain, optional string, never validated or auto-populated.

update_book/delete_book are owner-only, checked explicitly here (never
delegated to a UI-level "trust the button was hidden" assumption).
delete_book blocks on ANY loan history (not just active loans) — see
BookHasLoanHistoryError docstring.
"""
from __future__ import annotations

import datetime as dt
import json
import logging

logger = logging.getLogger(__name__)

from dataclasses import asdict, dataclass
from sqlalchemy import or_, select
from ..core.exceptions import (
    BookHasLoanHistoryError,
    BookHasPendingLoanRequestError,
    InvalidBookDataError,
    InvalidSearchQueryError,
    IsbnNotFoundError,
    NotAuthorizedError,
    NotFoundError,
)
from .external.open_library_client import fetch_book_by_isbn
from .external.open_library_search_client import search_books_raw
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.book import Book
from ..models.enums import RequestStatus
from ..models.enums import BookGenre, BorrowingVisibility
from ..models.group import GroupMembership
from ..models.loan import Loan
from ..models.loan_request import LoanRequest
from ..models.user import User
from ..core.exceptions import SummaryGenerationError
from ..models.enums import SummarySource
from .external.gemini_client import embed_text, generate_text
from . import authz_service

@dataclass(frozen=True)
class BookMetadataResult:
    """Metadata fetched from Open Library — read-only, never
    persisted automatically. The caller (state/UI) decides whether to
    use it to prefill the Add Book form.
    """

    title: str
    author: str | None
    publisher: str | None
    publish_date: str | None
    cover_url: str | None

    def to_dict(self) -> dict:
        return asdict(self)
    
@dataclass(frozen=True)
class BookSearchResult:
    """One possible match from a title search — distinct from
    BookMetadataResult ("a resolved book"). Multiple of these may exist
    for the same underlying work (editions, translations, revisions);
    the user picks one, never an automatic first choice.
    """

    work_key: str
    title: str
    author: str | None
    publish_year: int | None
    edition_count: int | None
    cover_id: int | None
    isbn: str | None

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class BookResult:
    id: int
    owner_id: int
    title: str
    author: str | None
    isbn: str | None
    location: str | None
    genre: str | None
    borrowing_visibility: str
    created_at: dt.datetime
    summary: str | None
    summary_source: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def _to_result(book: Book) -> BookResult:
    return BookResult(
        id=book.id,
        owner_id=book.owner_id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        location=book.location,
        genre=book.genre.value if book.genre else None,
        borrowing_visibility=book.borrowing_visibility.value,
        created_at=book.created_at,
        summary=book.summary,
        summary_source=book.summary_source.value if book.summary_source else None,
    )


def create_book(
    owner_id: int,
    title: str,
    author: str | None = None,
    isbn: str | None = None,
    location: str | None = None,
    genre: str | None = None,
    borrowing_visibility: str | None = None,
) -> BookResult:
    """Raises: NotFoundError, InvalidBookDataError, EmailNotVerifiedError."""
    authz_service.require_verified_email(owner_id)

    stripped_title = blank_to_none(title)
    if stripped_title is None:
        raise InvalidBookDataError("Book title must not be blank.")
    with get_session() as session:
        owner = session.get(User, owner_id)
        if owner is None:
            raise NotFoundError(f"User {owner_id} does not exist.")
        book = Book(
            owner_id=owner_id,
            title=stripped_title,
            author=blank_to_none(author),
            isbn=blank_to_none(isbn),
            location=blank_to_none(location),
            genre=BookGenre(genre) if genre else None,
            borrowing_visibility=BorrowingVisibility(borrowing_visibility) if borrowing_visibility else BorrowingVisibility.CLUB_ONLY,
        )
        session.add(book)
        session.flush()
        return _to_result(book)
    
def lookup_isbn(isbn: str) -> BookMetadataResult:
    """Fetch book metadata from Open Library for a given ISBN.

    Raises:
        IsbnNotFoundError: if Open Library has no record for this ISBN.

    Network/timeout failures propagate as requests.RequestException —
    not translated into a domain exception here, per the Service
    Contract (infrastructure failures stay infrastructure failures).
    """
    stripped_isbn = blank_to_none(isbn)
    if stripped_isbn is None:
        raise IsbnNotFoundError("No ISBN provided.")

    stripped_isbn = blank_to_none(isbn)
    if stripped_isbn is None:
        raise IsbnNotFoundError("No ISBN provided.")

    normalized_isbn = stripped_isbn.replace("-", "").replace(" ", "")

    raw = fetch_book_by_isbn(normalized_isbn)
    if raw is None:
        raise IsbnNotFoundError(f"No Open Library record found for ISBN {normalized_isbn}.")

    authors = raw.get("authors") or []
    author_names = ", ".join(a.get("name", "") for a in authors if a.get("name"))

    publishers = raw.get("publishers") or []
    publisher_name = publishers[0].get("name") if publishers else None

    cover = raw.get("cover") or {}
    cover_url = cover.get("medium") or cover.get("small") or cover.get("large")

    return BookMetadataResult(
        title=raw.get("title", ""),
        author=author_names or None,
        publisher=publisher_name,
        publish_date=raw.get("publish_date"),
        cover_url=cover_url,
    )

def search_books(query: str, limit: int = 20) -> list[BookSearchResult]:
    """Search Open Library by free text (title, author, etc.).

    Returns a list of candidate matches — possibly empty (genuinely no
    results is not an error). The caller always presents results for
    the user to choose from; this function never guesses a "best" one.

    Raises:
        InvalidSearchQueryError: if query is blank.

    Network/timeout failures propagate as requests.RequestException —
    not translated into a domain exception, per the Service Contract.
    """
    stripped_query = blank_to_none(query)
    if stripped_query is None:
        raise InvalidSearchQueryError("Search query must not be blank.")

    docs = search_books_raw(stripped_query, limit=limit)

    results: list[BookSearchResult] = []
    for doc in docs:
        author_names = doc.get("author_name") or []
        isbns = doc.get("isbn") or []
        results.append(
            BookSearchResult(
                work_key=doc.get("key", ""),
                title=doc.get("title", ""),
                author=", ".join(author_names) if author_names else None,
                publish_year=doc.get("first_publish_year"),
                edition_count=doc.get("edition_count"),
                cover_id=doc.get("cover_i"),
                isbn=isbns[0] if isbns else None,
            )
        )
    return results


def update_book(
    book_id: int,
    owner_id: int,
    title: str,
    author: str | None = None,
    isbn: str | None = None,
    location: str | None = None,
    genre: str | None = None,
    borrowing_visibility: str | None = None,
) -> BookResult:
    """Update a book's metadata. Owner-only.
    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
        InvalidBookDataError: if title is blank.
        EmailNotVerifiedError: if owner_id's email is not verified.
    """
    authz_service.require_verified_email(owner_id)

    stripped_title = blank_to_none(title)
    if stripped_title is None:
        raise InvalidBookDataError("Book title must not be blank.")
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if book.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own book {book_id}.")

        book.title = stripped_title
        book.author = blank_to_none(author)
        book.isbn = blank_to_none(isbn)
        book.location = blank_to_none(location)
        book.genre = BookGenre(genre) if genre else None
        if borrowing_visibility is not None:
            book.borrowing_visibility = BorrowingVisibility(borrowing_visibility)
        session.flush()
        return _to_result(book)
def compute_and_store_embedding(session, book: Book) -> None:
    """Always ensures a book has a usable embedding, even without a
    visible Book.summary. If summary exists, embed it directly. If
    not, generate a throwaway description via Gemini purely to embed
    it — never stored as Book.summary, never shown to the user. The
    owner alone decides whether/when a visible summary exists (see
    the Synopsis Pipeline's "Generate with AI" button) — this must
    never silently fill that field.

    Failures here are never shown to the user (embedding is an
    enhancement, not core functionality) — but they ARE logged, so a
    systematic problem (e.g. a retired Gemini model, an extended
    outage) is discoverable rather than silently invisible.
    """
    text_to_embed = book.summary
    if not text_to_embed:
        author_part = f" by {book.author}" if book.author else ""
        genre_part = f" ({book.genre.value})" if book.genre else ""
        prompt = (
            f"In 2-3 sentences, describe the mood, themes, and setting "
            f"of the book \"{book.title}\"{author_part}{genre_part}. "
            f"This is for internal search purposes only."
        )
        try:
            text_to_embed = generate_text(prompt)
        except Exception:
            logger.exception(
                "Fallback description generation failed for book %s", book.id
            )
            text_to_embed = f"{book.title}{author_part}{genre_part}"

    try:
        vector = embed_text(text_to_embed, task_type="RETRIEVAL_DOCUMENT")
        book.embedding = json.dumps(vector)
    except Exception:
        logger.exception("Embedding computation failed for book %s", book.id)

def set_summary(book_id: int, owner_id: int, summary: str) -> BookResult:
    """Manually set a book's summary. Owner-only.

    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
        InvalidBookDataError: if summary is blank.
    """
    stripped = blank_to_none(summary)
    if stripped is None:
        raise InvalidBookDataError("Summary must not be blank.")

    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if book.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own book {book_id}.")

        book.summary = stripped
        book.summary_source = SummarySource.OWNER
        session.flush()
        compute_and_store_embedding(session, book)
        return _to_result(book)
       
def fetch_summary_from_open_library(book_id: int, owner_id: int) -> BookResult:
    """Best-effort: Open Library's description field is not reliably
    present (a known upstream limitation — see project vault). Owner-
    only.

    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
        InvalidBookDataError: if the book has no ISBN set.
        SummaryGenerationError: if Open Library has no description for
            this ISBN.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if book.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own book {book_id}.")
        if not book.isbn:
            raise InvalidBookDataError("This book has no ISBN set.")

        raw = fetch_book_by_isbn(book.isbn)
        description = None
        if raw:
            desc_field = raw.get("description")
            if isinstance(desc_field, dict):
                description = desc_field.get("value")
            elif isinstance(desc_field, str):
                description = desc_field
            if description is None:
                excerpts = raw.get("excerpts") or []
                if excerpts:
                    description = excerpts[0].get("text")

        stripped = blank_to_none(description)
        if stripped is None:
            raise SummaryGenerationError(
                "Open Library has no description available for this ISBN."
            )

        book.summary = stripped
        book.summary_source = SummarySource.OPEN_LIBRARY
        session.flush()
        compute_and_store_embedding(session, book)
        return _to_result(book)
     
def generate_summary_with_ai(book_id: int, owner_id: int) -> BookResult:
    """Generate a spoiler-free summary via Gemini. Owner-only.

    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
        SummaryGenerationError: if Gemini returns no usable text.

    Network/API failures propagate as requests.RequestException, not
    translated into a domain exception here.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if book.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own book {book_id}.")

        author_part = f" by {book.author}" if book.author else ""
        prompt = (
            f"Write a short, spoiler-free summary (2-3 sentences) of the "
            f"book \"{book.title}\"{author_part}. Do not reveal plot twists "
            f"or the ending."
        )
        try:
            generated = generate_text(prompt)
        except ValueError as e:
            raise SummaryGenerationError(str(e)) from e

        stripped = blank_to_none(generated)
        if stripped is None:
            raise SummaryGenerationError("AI generation returned no usable text.")

        book.summary = stripped
        book.summary_source = SummarySource.AI_GENERATED
        session.flush()
        compute_and_store_embedding(session, book)
        return _to_result(book)
       
def clear_summary(book_id: int, owner_id: int) -> BookResult:
    """Remove a book's summary entirely. Owner-only.

    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if book.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own book {book_id}.")

        book.summary = None
        book.summary_source = None
        session.flush()
        return _to_result(book)


def delete_book(book_id: int, owner_id: int) -> None:
    """Delete a book. Owner-only, blocked by any loan history or
    pending loan request.

    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
        BookHasLoanHistoryError: if any Loan (active or historical)
            references this book.
        BookHasPendingLoanRequestError: if a pending LoanRequest
            references this book.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if book.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own book {book_id}.")

        has_loan_history = (
            session.scalar(select(Loan.id).where(Loan.book_id == book_id).limit(1))
            is not None
        )
        if has_loan_history:
            raise BookHasLoanHistoryError(
                f"Book {book_id} has loan history and cannot be deleted."
            )

        has_pending_request = (
            session.scalar(
                select(LoanRequest.id).where(
                    LoanRequest.book_id == book_id,
                    LoanRequest.status == RequestStatus.PENDING,
                ).limit(1)
            )
            is not None
        )
        if has_pending_request:
            raise BookHasPendingLoanRequestError(
                f"Book {book_id} has a pending loan request and cannot be deleted."
            )

        session.delete(book)
        session.flush()


def get_book(requester_id: int, book_id: int) -> BookResult:
    """Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if requester_id cannot view this book
            (not the owner, and shares no club with the owner) — per
            the 07.08. security review, project vault.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        if not authz_service.can_view_book(session, requester_id, book):
            raise NotAuthorizedError(
                f"User {requester_id} cannot view book {book_id}."
            )
        return _to_result(book)


def list_books() -> list[BookResult]:
    with get_session() as session:
        books = session.scalars(select(Book).order_by(Book.created_at)).all()
        return [_to_result(book) for book in books]


def list_books_for_owner(
    owner_id: int, search: str | None = None, genre: str | None = None
) -> list[BookResult]:
    """A single user's own catalogue — "My Personal Library".

    search matches title, author, isbn, or location (case-insensitive,
    substring match) — one universal field instead of separate inputs
    per data type, per Andy's request.
    """
    with get_session() as session:
        query = select(Book).where(Book.owner_id == owner_id)
        query = _apply_search_and_genre(query, search, genre)
        books = session.scalars(query.order_by(Book.created_at)).all()
        return [_to_result(book) for book in books]


def list_books_for_group(
    group_id: int, search: str | None = None, genre: str | None = None
) -> list[BookResult]:
    """Every book owned by any member of the given group —
    "Common/Club Library".
    """
    with get_session() as session:
        query = (
            select(Book)
            .join(GroupMembership, GroupMembership.user_id == Book.owner_id)
            .where(GroupMembership.group_id == group_id)
        )
        query = _apply_search_and_genre(query, search, genre)
        books = session.scalars(query.order_by(Book.created_at)).all()
        return [_to_result(book) for book in books]


def _apply_search_and_genre(query, search: str | None, genre: str | None):
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Book.title.ilike(pattern),
                Book.author.ilike(pattern),
                Book.isbn.ilike(pattern),
                Book.location.ilike(pattern),
                Book.genre.ilike(pattern),
            )
        )
    if genre:
        query = query.where(Book.genre == BookGenre(genre))
    return query


__all__ = [
    "BookResult",
    "create_book",
    "update_book",
    "delete_book",
    "get_book",
    "list_books",
    "list_books_for_owner",
    "list_books_for_group",
    "BookMetadataResult",
    "lookup_isbn",
    "BookSearchResult",
    "search_books",
    "set_summary",
    "fetch_summary_from_open_library",
    "generate_summary_with_ai",
    "clear_summary",
]