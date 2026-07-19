"""Book service. Per the Service Contract (Implementation
Specification.md): plain inputs, dataclass return values, domain
exceptions, self-contained transactions, no Reflex import.

Open Library ISBN lookup is deferred (Decorative-Assets-Gate /
"Deferred Until Core Is Green") — isbn here is accepted only as a
plain, optional string, never validated or auto-populated.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import select

from ..core.exceptions import InvalidBookDataError, NotFoundError
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.book import Book
from ..models.user import User


@dataclass(frozen=True)
class BookResult:
    """Plain data returned to callers — never a raw ORM instance, per
    the Service Contract.
    """

    id: int
    owner_id: int
    title: str
    author: str | None
    isbn: str | None
    created_at: dt.datetime


def _to_result(book: Book) -> BookResult:
    return BookResult(
        id=book.id,
        owner_id=book.owner_id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        created_at=book.created_at,
    )


def create_book(
    owner_id: int,
    title: str,
    author: str | None = None,
    isbn: str | None = None,
) -> BookResult:
    """Add a book to an owner's catalogue.

    Raises:
        NotFoundError: if the owner does not exist.
        InvalidBookDataError: if title is blank.
    """
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
        )
        session.add(book)
        session.flush()
        return _to_result(book)


def get_book(book_id: int) -> BookResult:
    """Fetch a single book.

    Raises:
        NotFoundError: if the book does not exist.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        return _to_result(book)


def list_books() -> list[BookResult]:
    """List all books, ordered by creation time.

    Phase 2 scope: no group/visibility filtering yet — that arrives
    with the group/membership UI in a later phase.
    """
    with get_session() as session:
        books = session.scalars(select(Book).order_by(Book.created_at)).all()
        return [_to_result(book) for book in books]


__all__ = ["BookResult", "create_book", "get_book", "list_books"]