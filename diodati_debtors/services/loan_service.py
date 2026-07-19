"""Loan service — the only place allowed to decide whether a loan may
be created or returned. Per the Service Contract (Implementation
Specification.md): plain inputs, dataclass return values, domain
exceptions, self-contained transactions, no Reflex import.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

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

        # Explicit existence check, consistent with the Book check
        # above — not delegated to the FK constraint, so the caller
        # gets a clear domain exception instead of an IntegrityError.
        borrower = session.get(User, borrower_id)
        if borrower is None:
            raise NotFoundError(f"User {borrower_id} does not exist.")

        # Business rule enforced here, against current DB state — never
        # against an already-loaded ORM object (Struktur.md, is_active
        # note). This check-then-insert is not fully race-proof under
        # true concurrent writes; acceptable for this project's scale.
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
        session.flush()  # populate loan.id before the session closes
        return _to_result(loan)


def return_loan(loan_id: int, return_date: dt.date | None = None) -> LoanResult:
    """Mark a loan as returned.

    `return_date` defaults to today (via core.time.today), per the same
    Date-Source-Policy as `create_loan`.

    Raises:
        NotFoundError: if the loan does not exist.
        LoanAlreadyReturnedError: if the loan already has a return_date
            — loan history is immutable, this is never silently
            overwritten.
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


__all__ = ["LoanResult", "create_loan", "return_loan"]