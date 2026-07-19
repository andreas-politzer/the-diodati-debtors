"""Loan service — the only place allowed to decide whether a loan may
be created or returned. Per the Service Contract (Implementation
Specification.md): plain inputs, dataclass return values, domain
exceptions, self-contained transactions, no Reflex import.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import (
    BookAlreadyOnLoanError,
    InvalidLoanDatesError,
    LoanAlreadyReturnedError,
    NotFoundError,
)
from ..core.time import today
from ..db.session import get_session
from ..models.book import Book
from ..models.loan import Loan
from ..models.user import User


@dataclass(frozen=True)
class LoanResult:
    """Plain data returned to callers — never a raw ORM instance, per
    the Service Contract (avoids detached-instance/session-lifecycle
    issues once the session that created it has closed).
    """

    id: int
    book_id: int
    borrower_id: int
    loan_date: dt.date
    due_date: dt.date
    return_date: dt.date | None

    @property
    def is_active(self) -> bool:
        return self.return_date is None

    def to_dict(self) -> dict:
        """Explicit serialization boundary — callers (state/) depend on
        this method, never on dataclasses.asdict() directly, so the
        internal representation can change without breaking callers.
        """
        return asdict(self)


def _to_result(loan: Loan) -> LoanResult:
    return LoanResult(
        id=loan.id,
        book_id=loan.book_id,
        borrower_id=loan.borrower_id,
        loan_date=loan.loan_date,
        due_date=loan.due_date,
        return_date=loan.return_date,
    )


def create_loan(
    book_id: int,
    borrower_id: int,
    due_date: dt.date,
    loan_date: dt.date | None = None,
) -> LoanResult:
    """Create a new loan for a book.

    `loan_date` defaults to today (via core.time.today, never a
    user-supplied "today" from the UI layer — see Date-Source-Policy).

    Raises:
        NotFoundError: if the book or borrower does not exist.
        InvalidLoanDatesError: if due_date < loan_date.
        BookAlreadyOnLoanError: if the book already has an active loan.
    """
    resolved_loan_date = loan_date or today()

    if due_date < resolved_loan_date:
        raise InvalidLoanDatesError(
            f"due_date ({due_date}) may not precede loan_date "
            f"({resolved_loan_date})."
        )

    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")

        borrower = session.get(User, borrower_id)
        if borrower is None:
            raise NotFoundError(f"User {borrower_id} does not exist.")

        active_loan = session.scalar(
            select(Loan).where(Loan.book_id == book_id, Loan.return_date.is_(None))
        )
        if active_loan is not None:
            raise BookAlreadyOnLoanError(
                f"Book {book_id} already has an active loan (loan_id={active_loan.id})."
            )

        loan = Loan(
            book_id=book_id,
            borrower_id=borrower_id,
            loan_date=resolved_loan_date,
            due_date=due_date,
            return_date=None,
        )
        session.add(loan)
        session.flush()
        return _to_result(loan)


def return_loan(loan_id: int, return_date: dt.date | None = None) -> LoanResult:
    """Mark a loan as returned.

    Raises:
        NotFoundError: if the loan does not exist.
        LoanAlreadyReturnedError: if the loan already has a return_date.
        InvalidLoanDatesError: if return_date < loan_date.
    """
    resolved_return_date = return_date or today()

    with get_session() as session:
        loan = session.get(Loan, loan_id)
        if loan is None:
            raise NotFoundError(f"Loan {loan_id} does not exist.")

        if loan.return_date is not None:
            raise LoanAlreadyReturnedError(
                f"Loan {loan_id} was already returned on {loan.return_date}."
            )

        if resolved_return_date < loan.loan_date:
            raise InvalidLoanDatesError(
                f"return_date ({resolved_return_date}) may not precede "
                f"loan_date ({loan.loan_date})."
            )

        loan.return_date = resolved_return_date
        session.flush()
        return _to_result(loan)


def get_active_loan_for_book(book_id: int) -> LoanResult | None:
    """Return the active loan for a single book, or None if available.

    Read-only lookup — for a single book. Use
    get_active_loans_for_books() when checking many books at once, to
    avoid N+1 calls.
    """
    with get_session() as session:
        active_loan = session.scalar(
            select(Loan).where(Loan.book_id == book_id, Loan.return_date.is_(None))
        )
        return _to_result(active_loan) if active_loan is not None else None


def get_active_loans_for_books(book_ids: list[int]) -> dict[int, LoanResult]:
    """Return active loans for a set of books in a single query.

    Used by state/ to avoid an N+1 pattern when rendering a book list
    with loan status attached. Books with no active loan are simply
    absent from the returned mapping.
    """
    if not book_ids:
        return {}
    with get_session() as session:
        active_loans = session.scalars(
            select(Loan).where(Loan.book_id.in_(book_ids), Loan.return_date.is_(None))
        ).all()
        return {loan.book_id: _to_result(loan) for loan in active_loans}

def list_loans_for_book(book_id: int) -> list[LoanResult]:
    """All loans (active and historical) for a book, most recent first.

    Read-only — used by the book detail page to show loan history.
    """
    with get_session() as session:
        loans = session.scalars(
            select(Loan).where(Loan.book_id == book_id).order_by(Loan.loan_date.desc())
        ).all()
        return [_to_result(loan) for loan in loans]

__all__ = [
    "LoanResult",
    "create_loan",
    "return_loan",
    "get_active_loan_for_book",
    "get_active_loans_for_books",
    "list_loans_for_book",
]