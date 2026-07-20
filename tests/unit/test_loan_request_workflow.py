"""Tests for the loan-request/approval workflow in loan_service:
request_to_borrow, approve_loan_request, decline_loan_request.

Complements test_loan_service.py, which covers create_loan/return_loan
directly (still used internally, e.g. by approve_loan_request).
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import (
    BookAlreadyOnLoanError,
    CannotRequestOwnBookError,
    DuplicateLoanRequestError,
    NotAuthorizedError,
    RequestNotPendingError,
)
from diodati_debtors.models.book import Book
from diodati_debtors.models.enums import RequestStatus
from diodati_debtors.models.loan import Loan
from diodati_debtors.models.user import User
from diodati_debtors.services import loan_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="Reader")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_book(db, owner_id: int, title: str) -> int:
    with db() as session:
        book = Book(owner_id=owner_id, title=title)
        session.add(book)
        session.commit()
        session.refresh(book)
        return book.id


def test_request_to_borrow_succeeds(db):
    owner_id = _make_user(db, "owner1@example.com")
    requester_id = _make_user(db, "requester1@example.com")
    book_id = _make_book(db, owner_id, "Frankenstein")

    result = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    assert result.status == RequestStatus.PENDING.value


def test_request_to_borrow_rejects_own_book(db):
    owner_id = _make_user(db, "owner2@example.com")
    book_id = _make_book(db, owner_id, "Dracula")

    with pytest.raises(CannotRequestOwnBookError):
        loan_service.request_to_borrow(book_id=book_id, requester_id=owner_id)


def test_request_to_borrow_rejects_book_already_on_loan(db):
    owner_id = _make_user(db, "owner3@example.com")
    borrower_id = _make_user(db, "borrower3@example.com")
    requester_id = _make_user(db, "requester3@example.com")
    book_id = _make_book(db, owner_id, "The Vampyre")
    import datetime as dt
    loan_service.create_loan(
        book_id=book_id, borrower_id=borrower_id, due_date=dt.date.today() + dt.timedelta(days=14)
    )

    with pytest.raises(BookAlreadyOnLoanError):
        loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)


def test_request_to_borrow_rejects_duplicate_pending_request(db):
    owner_id = _make_user(db, "owner4@example.com")
    requester_id = _make_user(db, "requester4@example.com")
    book_id = _make_book(db, owner_id, "Carmilla")
    loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    with pytest.raises(DuplicateLoanRequestError):
        loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)


def test_approve_loan_request_creates_loan(db):
    owner_id = _make_user(db, "owner5@example.com")
    requester_id = _make_user(db, "requester5@example.com")
    book_id = _make_book(db, owner_id, "Melmoth the Wanderer")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    result = loan_service.approve_loan_request(request.id, reviewer_id=owner_id)

    assert result.status == RequestStatus.APPROVED.value
    with db() as session:
        loan = session.query(Loan).filter_by(book_id=book_id).one()
        assert loan.borrower_id == requester_id
        assert loan.return_date is None


def test_approve_loan_request_rejects_non_owner_reviewer(db):
    owner_id = _make_user(db, "owner6@example.com")
    requester_id = _make_user(db, "requester6@example.com")
    outsider_id = _make_user(db, "outsider6@example.com")
    book_id = _make_book(db, owner_id, "The Monk")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    with pytest.raises(NotAuthorizedError):
        loan_service.approve_loan_request(request.id, reviewer_id=outsider_id)


def test_approve_loan_request_rejects_already_reviewed(db):
    owner_id = _make_user(db, "owner7@example.com")
    requester_id = _make_user(db, "requester7@example.com")
    book_id = _make_book(db, owner_id, "Vathek")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)
    loan_service.approve_loan_request(request.id, reviewer_id=owner_id)

    with pytest.raises(RequestNotPendingError):
        loan_service.approve_loan_request(request.id, reviewer_id=owner_id)


def test_approve_loan_request_rejects_when_book_already_on_loan(db):
    """Race-condition coverage: if the book somehow already has an
    active loan by the time of approval (e.g. two concurrent requests
    both approved), approval must fail cleanly.
    """
    owner_id = _make_user(db, "owner8@example.com")
    requester_id = _make_user(db, "requester8@example.com")
    other_borrower_id = _make_user(db, "otherborrower8@example.com")
    book_id = _make_book(db, owner_id, "Zofloya")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    # Simulate the book being lent out directly in the meantime.
    import datetime as dt
    loan_service.create_loan(
        book_id=book_id, borrower_id=other_borrower_id, due_date=dt.date.today() + dt.timedelta(days=14)
    )

    with pytest.raises(BookAlreadyOnLoanError):
        loan_service.approve_loan_request(request.id, reviewer_id=owner_id)


def test_decline_loan_request_creates_no_loan(db):
    owner_id = _make_user(db, "owner9@example.com")
    requester_id = _make_user(db, "requester9@example.com")
    book_id = _make_book(db, owner_id, "The Castle of Otranto")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    result = loan_service.decline_loan_request(request.id, reviewer_id=owner_id)

    assert result.status == RequestStatus.DECLINED.value
    with db() as session:
        count = session.query(Loan).filter_by(book_id=book_id).count()
        assert count == 0