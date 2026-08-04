"""Tests for the loan-request/approval workflow in loan_service:
request_to_borrow, approve_loan_request, decline_loan_request.

Complements test_loan_service.py, which covers create_loan/return_loan
directly (still used internally, e.g. by approve_loan_request).
"""

from __future__ import annotations

import pytest
import datetime as dt

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


def _make_user(db, email: str, *, verified: bool = True) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User", email_verified=verified)
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

def test_request_to_borrow_with_custom_due_date_and_note(db):
    owner_id = _make_user(db, "owner_custom1@example.com")
    requester_id = _make_user(db, "requester_custom1@example.com")
    book_id = _make_book(db, owner_id, "Vacation Book")

    custom_due_date = dt.date.today() + dt.timedelta(days=21)
    result = loan_service.request_to_borrow(
        book_id=book_id,
        requester_id=requester_id,
        requested_due_date=custom_due_date,
        note="I'm on vacation for three weeks.",
    )

    assert result.requested_due_date == custom_due_date
    assert result.note == "I'm on vacation for three weeks."


def test_request_to_borrow_without_custom_period_leaves_fields_none(db):
    owner_id = _make_user(db, "owner_custom2@example.com")
    requester_id = _make_user(db, "requester_custom2@example.com")
    book_id = _make_book(db, owner_id, "Standard Book")

    result = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    assert result.requested_due_date is None
    assert result.note is None


def test_approve_loan_request_uses_requested_due_date_when_provided(db):
    owner_id = _make_user(db, "owner_custom3@example.com")
    requester_id = _make_user(db, "requester_custom3@example.com")
    book_id = _make_book(db, owner_id, "Custom Period Book")

    custom_due_date = dt.date.today() + dt.timedelta(days=30)
    request = loan_service.request_to_borrow(
        book_id=book_id, requester_id=requester_id, requested_due_date=custom_due_date,
    )
    loan_service.approve_loan_request(request.id, reviewer_id=owner_id)

    with db() as session:
        from diodati_debtors.models.loan import Loan
        loan = session.query(Loan).filter_by(book_id=book_id).one()
        assert loan.due_date == custom_due_date

def test_approve_loan_request_with_response_message(db):
    owner_id = _make_user(db, "owner_response1@example.com")
    requester_id = _make_user(db, "requester_response1@example.com")
    book_id = _make_book(db, owner_id, "Friendly Book")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    result = loan_service.approve_loan_request(
        request.id, reviewer_id=owner_id,
        response_message="Sure, come pick it up after 5pm.",
    )

    assert result.response_message == "Sure, come pick it up after 5pm."


def test_decline_loan_request_with_response_message(db):
    owner_id = _make_user(db, "owner_response2@example.com")
    requester_id = _make_user(db, "requester_response2@example.com")
    book_id = _make_book(db, owner_id, "Keep it Book")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    result = loan_service.decline_loan_request(
        request.id, reviewer_id=owner_id,
        response_message="Sorry, wanted to take it on vacation myself.",
    )

    assert result.response_message == "Sorry, wanted to take it on vacation myself."


def test_list_loan_requests_for_requester_returns_all_statuses(db):
    owner_id = _make_user(db, "owner_response3@example.com")
    requester_id = _make_user(db, "requester_response3@example.com")
    book_a = _make_book(db, owner_id, "Book A")
    book_b = _make_book(db, owner_id, "Book B")

    request_a = loan_service.request_to_borrow(book_id=book_a, requester_id=requester_id)
    request_b = loan_service.request_to_borrow(book_id=book_b, requester_id=requester_id)
    loan_service.decline_loan_request(request_b.id, reviewer_id=owner_id)

    results = loan_service.list_loan_requests_for_requester(requester_id)

    assert {r.id for r in results} == {request_a.id, request_b.id}

def test_mark_loan_request_response_read(db):
    owner_id = _make_user(db, "owner_read1@example.com")
    requester_id = _make_user(db, "requester_read1@example.com")
    book_id = _make_book(db, owner_id, "Some Book")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)
    loan_service.approve_loan_request(request.id, reviewer_id=owner_id, response_message="Sure!")

    result = loan_service.mark_loan_request_response_read(request.id, requester_id=requester_id)

    assert result.response_read is True


def test_mark_loan_request_response_read_rejects_non_requester(db):
    owner_id = _make_user(db, "owner_read2@example.com")
    requester_id = _make_user(db, "requester_read2@example.com")
    outsider_id = _make_user(db, "outsider_read1@example.com")
    book_id = _make_book(db, owner_id, "Another Book")
    request = loan_service.request_to_borrow(book_id=book_id, requester_id=requester_id)

    with pytest.raises(NotAuthorizedError):
        loan_service.mark_loan_request_response_read(request.id, requester_id=outsider_id)