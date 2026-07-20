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
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import (
    BookHasLoanHistoryError,
    BookHasPendingLoanRequestError,
    InvalidBookDataError,
    NotAuthorizedError,
    NotFoundError,
)
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.book import Book
from ..models.enums import RequestStatus
from ..models.group import GroupMembership
from ..models.loan import Loan
from ..models.loan_request import LoanRequest
from ..models.user import User


@dataclass(frozen=True)
class BookResult:
    id: int
    owner_id: int
    title: str
    author: str | None
    isbn: str | None
    location: str | None
    created_at: dt.datetime

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
        created_at=book.created_at,
    )


def create_book(
    owner_id: int,
    title: str,
    author: str | None = None,
    isbn: str | None = None,
    location: str | None = None,
) -> BookResult:
    """Raises: NotFoundError, InvalidBookDataError."""
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
        )
        session.add(book)
        session.flush()
        return _to_result(book)


def update_book(
    book_id: int,
    owner_id: int,
    title: str,
    author: str | None = None,
    isbn: str | None = None,
    location: str | None = None,
) -> BookResult:
    """Update a book's metadata. Owner-only.

    Raises:
        NotFoundError: if the book does not exist.
        NotAuthorizedError: if owner_id does not own the book.
        InvalidBookDataError: if title is blank.
    """
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


def get_book(book_id: int) -> BookResult:
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        return _to_result(book)


def list_books() -> list[BookResult]:
    with get_session() as session:
        books = session.scalars(select(Book).order_by(Book.created_at)).all()
        return [_to_result(book) for book in books]


def list_books_for_owner(owner_id: int) -> list[BookResult]:
    with get_session() as session:
        books = session.scalars(
            select(Book).where(Book.owner_id == owner_id).order_by(Book.created_at)
        ).all()
        return [_to_result(book) for book in books]


def list_books_for_group(group_id: int) -> list[BookResult]:
    with get_session() as session:
        books = session.scalars(
            select(Book)
            .join(GroupMembership, GroupMembership.user_id == Book.owner_id)
            .where(GroupMembership.group_id == group_id)
            .order_by(Book.created_at)
        ).all()
        return [_to_result(book) for book in books]


__all__ = [
    "BookResult",
    "create_book",
    "update_book",
    "delete_book",
    "get_book",
    "list_books",
    "list_books_for_owner",
    "list_books_for_group",
]