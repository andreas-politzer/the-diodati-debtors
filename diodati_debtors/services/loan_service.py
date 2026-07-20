"""Loan service — the only place allowed to decide whether a loan may
be created or returned, and now also the loan-request/approval
workflow. Per the Service Contract: plain inputs, dataclass return
values, domain exceptions, self-contained transactions, no Reflex
import.

LoanRequest is a distinct entity from Loan (Domain Model v2, project
vault): a request may be declined, cancelled, or expire without ever
becoming a Loan. This replaces the previous instant "Lend to" flow —
the owner must approve before a Loan is created. Approved/declined
requests are never deleted — immutable history, same principle as
Loan itself.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..core.exceptions import (
    BookAlreadyOnLoanError,
    CannotRequestOwnBookError,
    DuplicateLoanRequestError,
    InvalidLoanDatesError,
    LoanAlreadyReturnedError,
    NotAuthorizedError,
    NotFoundError,
    RequestNotPendingError,
)
from ..core.time import today, utcnow
from ..db.session import get_session
from ..models.book import Book
from ..models.enums import RequestStatus
from ..models.loan import Loan
from ..models.loan_request import LoanRequest
from ..models.user import User

DEFAULT_LOAN_PERIOD_DAYS = 14


@dataclass(frozen=True)
class LoanResult:
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
        return asdict(self)


@dataclass(frozen=True)
class LoanRequestResult:
    id: int
    book_id: int
    requester_id: int
    status: str
    requested_at: dt.datetime
    reviewed_at: dt.datetime | None
    reviewed_by: int | None

    def to_dict(self) -> dict:
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


def _to_request_result(request: LoanRequest) -> LoanRequestResult:
    return LoanRequestResult(
        id=request.id,
        book_id=request.book_id,
        requester_id=request.requester_id,
        status=request.status.value,
        requested_at=request.requested_at,
        reviewed_at=request.reviewed_at,
        reviewed_by=request.reviewed_by,
    )


def create_loan(
    book_id: int,
    borrower_id: int,
    due_date: dt.date,
    loan_date: dt.date | None = None,
) -> LoanResult:
    """Create a new loan for a book directly.

    Still used internally (e.g. by approve_loan_request) and available
    for any future entry point that legitimately bypasses the request
    workflow. Not exposed to end users directly anymore in the UI —
    lending now goes through request_to_borrow + approve_loan_request.

    Raises:
        NotFoundError: if the book or borrower does not exist.
        InvalidLoanDatesError: if due_date < loan_date.
        BookAlreadyOnLoanError: if the book already has an active loan.
    """
    resolved_loan_date = loan_date or today()

    if due_date < resolved_loan_date:
        raise InvalidLoanDatesError(
            f"due_date ({due_date}) may not precede loan_date ({resolved_loan_date})."
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
        LoanAlreadyReturnedError: if already returned.
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
                f"return_date ({resolved_return_date}) may not precede loan_date ({loan.loan_date})."
            )

        loan.return_date = resolved_return_date
        session.flush()
        return _to_result(loan)


def get_active_loan_for_book(book_id: int) -> LoanResult | None:
    with get_session() as session:
        active_loan = session.scalar(
            select(Loan).where(Loan.book_id == book_id, Loan.return_date.is_(None))
        )
        return _to_result(active_loan) if active_loan is not None else None


def get_active_loans_for_books(book_ids: list[int]) -> dict[int, LoanResult]:
    if not book_ids:
        return {}
    with get_session() as session:
        active_loans = session.scalars(
            select(Loan).where(Loan.book_id.in_(book_ids), Loan.return_date.is_(None))
        ).all()
        return {loan.book_id: _to_result(loan) for loan in active_loans}


def list_loans_for_book(book_id: int) -> list[LoanResult]:
    with get_session() as session:
        loans = session.scalars(
            select(Loan).where(Loan.book_id == book_id).order_by(Loan.loan_date.desc())
        ).all()
        return [_to_result(loan) for loan in loans]


# --- Loan-request workflow -------------------------------------------------


def request_to_borrow(book_id: int, requester_id: int) -> LoanRequestResult:
    """Submit a request to borrow a book.

    Raises:
        NotFoundError: if the book or requester does not exist.
        CannotRequestOwnBookError: if the requester owns the book.
        BookAlreadyOnLoanError: if the book already has an active loan
            (requesting an already-loaned book is a Reservation concept
            — deferred, see Domain Model v2 — not a LoanRequest).
        DuplicateLoanRequestError: if the requester already has a
            PENDING request for this book.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        requester = session.get(User, requester_id)
        if requester is None:
            raise NotFoundError(f"User {requester_id} does not exist.")

        if book.owner_id == requester_id:
            raise CannotRequestOwnBookError(
                f"User {requester_id} owns book {book_id} and cannot request it."
            )

        active_loan = session.scalar(
            select(Loan).where(Loan.book_id == book_id, Loan.return_date.is_(None))
        )
        if active_loan is not None:
            raise BookAlreadyOnLoanError(
                f"Book {book_id} already has an active loan (loan_id={active_loan.id})."
            )

        pending_request = session.scalar(
            select(LoanRequest).where(
                LoanRequest.book_id == book_id,
                LoanRequest.requester_id == requester_id,
                LoanRequest.status == RequestStatus.PENDING,
            )
        )
        if pending_request is not None:
            raise DuplicateLoanRequestError(
                f"User {requester_id} already has a pending request for book {book_id}."
            )

        request = LoanRequest(book_id=book_id, requester_id=requester_id)
        session.add(request)
        session.flush()
        return _to_request_result(request)


def list_pending_loan_requests_for_book(book_id: int) -> list[LoanRequestResult]:
    with get_session() as session:
        requests = session.scalars(
            select(LoanRequest)
            .where(
                LoanRequest.book_id == book_id,
                LoanRequest.status == RequestStatus.PENDING,
            )
            .order_by(LoanRequest.requested_at)
        ).all()
        return [_to_request_result(r) for r in requests]


def get_pending_request_book_ids_for_requester(
    book_ids: list[int], requester_id: int
) -> set[int]:
    """Which of the given books already have a PENDING request from
    this requester — a single batched query, used by state/ to avoid
    an N+1 pattern when rendering a book list (same discipline as
    get_active_loans_for_books).
    """
    if not book_ids:
        return set()
    with get_session() as session:
        rows = session.scalars(
            select(LoanRequest.book_id).where(
                LoanRequest.book_id.in_(book_ids),
                LoanRequest.requester_id == requester_id,
                LoanRequest.status == RequestStatus.PENDING,
            )
        ).all()
        return set(rows)


def _ensure_can_review_loan_request(session, book_id: int, reviewer_id: int) -> None:
    book = session.get(Book, book_id)
    if book is None or book.owner_id != reviewer_id:
        raise NotAuthorizedError(
            f"User {reviewer_id} is not authorized to review requests for book {book_id}."
        )


def approve_loan_request(
    request_id: int,
    reviewer_id: int,
    due_in_days: int = DEFAULT_LOAN_PERIOD_DAYS,
) -> LoanRequestResult:
    """Approve a pending loan request, creating the resulting Loan.

    Raises:
        NotFoundError: if the request does not exist.
        NotAuthorizedError: if reviewer_id does not own the book.
        RequestNotPendingError: if the request isn't currently PENDING.
        BookAlreadyOnLoanError: if the book somehow already has an
            active loan by the time of approval (race condition —
            checked explicitly, not left to surface as a raw
            IntegrityError, per the Service Contract).
    """
    with get_session() as session:
        request = session.get(LoanRequest, request_id)
        if request is None:
            raise NotFoundError(f"LoanRequest {request_id} does not exist.")

        _ensure_can_review_loan_request(session, request.book_id, reviewer_id)

        if request.status != RequestStatus.PENDING:
            raise RequestNotPendingError(
                f"LoanRequest {request_id} is not pending (status={request.status})."
            )

        active_loan = session.scalar(
            select(Loan).where(
                Loan.book_id == request.book_id, Loan.return_date.is_(None)
            )
        )
        if active_loan is not None:
            raise BookAlreadyOnLoanError(
                f"Book {request.book_id} already has an active loan "
                f"(loan_id={active_loan.id})."
            )

        request.status = RequestStatus.APPROVED
        request.reviewed_at = utcnow()
        request.reviewed_by = reviewer_id

        loan = Loan(
            book_id=request.book_id,
            borrower_id=request.requester_id,
            loan_date=today(),
            due_date=today() + dt.timedelta(days=due_in_days),
            return_date=None,
        )
        session.add(loan)

        try:
            session.flush()
        except IntegrityError as e:
            session.rollback()
            raise BookAlreadyOnLoanError(
                f"Book {request.book_id} already has an active loan "
                f"(race condition: concurrent approval)."
            ) from e

        return _to_request_result(request)


def decline_loan_request(request_id: int, reviewer_id: int) -> LoanRequestResult:
    """Decline a pending loan request. No Loan is created.

    Raises:
        NotFoundError: if the request does not exist.
        NotAuthorizedError: if reviewer_id does not own the book.
        RequestNotPendingError: if the request isn't currently PENDING.
    """
    with get_session() as session:
        request = session.get(LoanRequest, request_id)
        if request is None:
            raise NotFoundError(f"LoanRequest {request_id} does not exist.")

        _ensure_can_review_loan_request(session, request.book_id, reviewer_id)

        if request.status != RequestStatus.PENDING:
            raise RequestNotPendingError(
                f"LoanRequest {request_id} is not pending (status={request.status})."
            )

        request.status = RequestStatus.DECLINED
        request.reviewed_at = utcnow()
        request.reviewed_by = reviewer_id
        session.flush()
        return _to_request_result(request)


__all__ = [
    "LoanResult",
    "LoanRequestResult",
    "create_loan",
    "return_loan",
    "get_active_loan_for_book",
    "get_active_loans_for_books",
    "list_loans_for_book",
    "request_to_borrow",
    "list_pending_loan_requests_for_book",
    "get_pending_request_book_ids_for_requester",
    "approve_loan_request",
    "decline_loan_request",
]