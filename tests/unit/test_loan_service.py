"""Tests for loan_service — required per Implementation Specification
Phase 2: successful loan, rejection of a second active loan for the
same book, successful return, and confirmation that the service layer
has no Reflex dependency.

Uses a fixed reference date throughout rather than dt.date.today(), so
tests are deterministic regardless of when they run (no midnight/
timezone edge cases, no dependency on the day of execution).
"""

from __future__ import annotations

import datetime as dt

import pytest

from diodati_debtors.core.exceptions import (
    BookAlreadyOnLoanError,
    LoanAlreadyReturnedError,
)
from diodati_debtors.models.book import Book
from diodati_debtors.models.user import User
from diodati_debtors.services import loan_service

REFERENCE_DATE = dt.date(2026, 7, 1)
DUE_DATE = REFERENCE_DATE + dt.timedelta(days=14)


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


def test_create_loan_succeeds(db):
    owner_id = _make_user(db, "owner1@example.com")
    borrower_id = _make_user(db, "borrower1@example.com")
    book_id = _make_book(db, owner_id, "Frankenstein")

    result = loan_service.create_loan(
        book_id=book_id,
        borrower_id=borrower_id,
        due_date=DUE_DATE,
        loan_date=REFERENCE_DATE,
    )

    assert result.book_id == book_id
    assert result.borrower_id == borrower_id
    assert result.loan_date == REFERENCE_DATE
    assert result.is_active is True


def test_create_loan_rejects_second_active_loan_for_same_book(db):
    owner_id = _make_user(db, "owner2@example.com")
    borrower_id = _make_user(db, "borrower2@example.com")
    book_id = _make_book(db, owner_id, "Dracula")

    loan_service.create_loan(
        book_id=book_id,
        borrower_id=borrower_id,
        due_date=DUE_DATE,
        loan_date=REFERENCE_DATE,
    )

    with pytest.raises(BookAlreadyOnLoanError):
        loan_service.create_loan(
            book_id=book_id,
            borrower_id=borrower_id,
            due_date=DUE_DATE,
            loan_date=REFERENCE_DATE,
        )


def test_return_loan_succeeds(db):
    owner_id = _make_user(db, "owner3@example.com")
    borrower_id = _make_user(db, "borrower3@example.com")
    book_id = _make_book(db, owner_id, "The Vampyre")

    created = loan_service.create_loan(
        book_id=book_id,
        borrower_id=borrower_id,
        due_date=DUE_DATE,
        loan_date=REFERENCE_DATE,
    )

    return_date = REFERENCE_DATE + dt.timedelta(days=5)
    returned = loan_service.return_loan(created.id, return_date=return_date)

    assert returned.is_active is False
    assert returned.return_date == return_date


def test_return_loan_rejects_double_return(db):
    owner_id = _make_user(db, "owner4@example.com")
    borrower_id = _make_user(db, "borrower4@example.com")
    book_id = _make_book(db, owner_id, "Frankenstein, Vol. 2")

    created = loan_service.create_loan(
        book_id=book_id,
        borrower_id=borrower_id,
        due_date=DUE_DATE,
        loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(created.id, return_date=REFERENCE_DATE + dt.timedelta(days=3))

    with pytest.raises(LoanAlreadyReturnedError):
        loan_service.return_loan(created.id, return_date=REFERENCE_DATE + dt.timedelta(days=4))

def test_list_loans_for_borrower_returns_active_and_historical(db):
    owner_id = _make_user(db, "owner_borrower1@example.com")
    borrower_id = _make_user(db, "borrower_borrower1@example.com")
    other_borrower_id = _make_user(db, "other_borrower1@example.com")
    active_book_id = _make_book(db, owner_id, "Currently Borrowed Book")
    returned_book_id = _make_book(db, owner_id, "Already Returned Book")

    active_loan = loan_service.create_loan(
        book_id=active_book_id,
        borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14),
        loan_date=REFERENCE_DATE,
    )
    returned_loan = loan_service.create_loan(
        book_id=returned_book_id,
        borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14),
        loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(returned_loan.id, return_date=REFERENCE_DATE + dt.timedelta(days=5))
    # A loan belonging to someone else must never show up.
    loan_service.create_loan(
        book_id=_make_book(db, owner_id, "Someone Else's Loan"),
        borrower_id=other_borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14),
        loan_date=REFERENCE_DATE,
    )

    results = loan_service.list_loans_for_borrower(borrower_id)

    assert {r.id for r in results} == {active_loan.id, returned_loan.id}
    assert any(r.is_active for r in results)
    assert any(not r.is_active for r in results)

def test_list_loans_for_owner_returns_only_that_owners_books_loans(db):
    owner_id = _make_user(db, "owner_lent1@example.com")
    other_owner_id = _make_user(db, "owner_lent2@example.com")
    borrower_id = _make_user(db, "borrower_lent1@example.com")
    my_book_id = _make_book(db, owner_id, "My Book")
    other_book_id = _make_book(db, other_owner_id, "Other Owner's Book")

    my_loan = loan_service.create_loan(
        book_id=my_book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.create_loan(
        book_id=other_book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )

    results = loan_service.list_loans_for_owner(owner_id)

    assert [r.id for r in results] == [my_loan.id]


def test_loan_service_has_no_reflex_dependency():
    """Static source check: the service module must never import
    reflex, per the Architecture Contract (services are framework-
    agnostic use cases, no reflex import).
    """
    with open(loan_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source