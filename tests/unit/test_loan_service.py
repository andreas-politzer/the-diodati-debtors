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
    LoanAlreadyReturnedError,NotAuthorizedError 
)
from diodati_debtors.models.book import Book
from diodati_debtors.models.user import User
from diodati_debtors.services import loan_service

REFERENCE_DATE = dt.date(2026, 7, 1)
DUE_DATE = REFERENCE_DATE + dt.timedelta(days=14)


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

def test_lend_to_contact_succeeds(db):
    from diodati_debtors.services import contact_service

    owner_id = _make_user(db, "owner_contact1@example.com")
    book_id = _make_book(db, owner_id, "Contact Book")
    contact = contact_service.create_contact(owner_id=owner_id, name="Grandma")

    result = loan_service.lend_to_contact(
        book_id=book_id, owner_id=owner_id, contact_id=contact.id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )

    assert result.contact_id == contact.id
    assert result.borrower_id is None


def test_lend_to_contact_rejects_non_owner_of_book(db):
    from diodati_debtors.services import contact_service

    owner_id = _make_user(db, "owner_contact2@example.com")
    outsider_id = _make_user(db, "outsider_contact1@example.com")
    book_id = _make_book(db, owner_id, "Protected Book")
    contact = contact_service.create_contact(owner_id=owner_id, name="Grandma")

    with pytest.raises(NotAuthorizedError):
        loan_service.lend_to_contact(
            book_id=book_id, owner_id=outsider_id, contact_id=contact.id,
            due_date=REFERENCE_DATE + dt.timedelta(days=14),
            loan_date=REFERENCE_DATE,
        )


def test_lend_to_contact_rejects_contact_belonging_to_someone_else(db):
    from diodati_debtors.services import contact_service

    owner_id = _make_user(db, "owner_contact3@example.com")
    other_owner_id = _make_user(db, "owner_contact4@example.com")
    book_id = _make_book(db, owner_id, "Some Book")
    someone_elses_contact = contact_service.create_contact(owner_id=other_owner_id, name="Not Yours")

    with pytest.raises(NotAuthorizedError):
        loan_service.lend_to_contact(
            book_id=book_id, owner_id=owner_id, contact_id=someone_elses_contact.id,
            due_date=REFERENCE_DATE + dt.timedelta(days=14),
            loan_date=REFERENCE_DATE,
        )


def test_lend_to_contact_rejects_book_already_on_loan(db):
    from diodati_debtors.services import contact_service

    owner_id = _make_user(db, "owner_contact5@example.com")
    borrower_id = _make_user(db, "borrower_contact1@example.com")
    book_id = _make_book(db, owner_id, "Busy Book")
    contact = contact_service.create_contact(owner_id=owner_id, name="Grandma")
    loan_service.create_loan(
        book_id=book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )

    with pytest.raises(BookAlreadyOnLoanError):
        loan_service.lend_to_contact(
            book_id=book_id, owner_id=owner_id, contact_id=contact.id,
            due_date=REFERENCE_DATE + dt.timedelta(days=14),
            loan_date=REFERENCE_DATE,
        )


def test_loan_service_has_no_reflex_dependency():
    """Static source check: the service module must never import
    reflex, per the Architecture Contract (services are framework-
    agnostic use cases, no reflex import).
    """
    with open(loan_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source