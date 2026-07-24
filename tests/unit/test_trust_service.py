"""Tests for trust_service: Reliability and Book Care computed on
demand, cold-start handling, weighted lateness, ignored unrated loans.
"""

from __future__ import annotations

import datetime as dt

from diodati_debtors.models.user import User
from diodati_debtors.services import book_service, loan_service, trust_service

REFERENCE_DATE = dt.date(2026, 7, 1)


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_book(db, owner_id: int, title: str) -> int:
    from diodati_debtors.models.book import Book

    with db() as session:
        book = Book(owner_id=owner_id, title=title)
        session.add(book)
        session.commit()
        session.refresh(book)
        return book.id


def test_new_member_has_no_negative_ratings(db):
    owner_id = _make_user(db, "owner1@example.com")
    borrower_id = _make_user(db, "borrower1@example.com")
    book_id = _make_book(db, owner_id, "Untouched Book")
    # Active loan only, never returned — should not count as completed.
    loan_service.create_loan(
        book_id=book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )

    signals = trust_service.get_trust_signals(borrower_id)

    assert signals.reliability == "New Member"
    assert signals.book_care == "Not Yet Rated"


def test_on_time_return_gives_excellent_reliability(db):
    owner_id = _make_user(db, "owner2@example.com")
    borrower_id = _make_user(db, "borrower2@example.com")
    book_id = _make_book(db, owner_id, "Punctual Book")
    loan = loan_service.create_loan(
        book_id=book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(loan.id, return_date=REFERENCE_DATE + dt.timedelta(days=14))

    signals = trust_service.get_trust_signals(borrower_id)

    assert signals.reliability == "Excellent"


def test_heavily_overdue_returns_give_needs_improvement(db):
    owner_id = _make_user(db, "owner3@example.com")
    borrower_id = _make_user(db, "borrower3@example.com")
    book_id = _make_book(db, owner_id, "Very Late Book")
    loan = loan_service.create_loan(
        book_id=book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(loan.id, return_date=REFERENCE_DATE + dt.timedelta(days=40))

    signals = trust_service.get_trust_signals(borrower_id)

    assert signals.reliability == "Needs Improvement"


def test_reliability_averages_across_multiple_loans(db):
    owner_id = _make_user(db, "owner4@example.com")
    borrower_id = _make_user(db, "borrower4@example.com")
    book_a = _make_book(db, owner_id, "Book A")
    book_b = _make_book(db, owner_id, "Book B")

    loan_a = loan_service.create_loan(
        book_id=book_a, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(loan_a.id, return_date=REFERENCE_DATE + dt.timedelta(days=14))  # on time: 100

    loan_b = loan_service.create_loan(
        book_id=book_b, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(loan_b.id, return_date=REFERENCE_DATE + dt.timedelta(days=16))  # 2 days late: 80

    # average (100+80)/2 = 90 -> Excellent
    signals = trust_service.get_trust_signals(borrower_id)

    assert signals.reliability == "Excellent"


def test_book_care_reflects_condition_rating(db):
    owner_id = _make_user(db, "owner5@example.com")
    borrower_id = _make_user(db, "borrower5@example.com")
    book_id = _make_book(db, owner_id, "Rated Book")
    loan = loan_service.create_loan(
        book_id=book_id, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(
        loan.id,
        return_date=REFERENCE_DATE + dt.timedelta(days=14),
        condition_rating="significantly_worse",
    )

    signals = trust_service.get_trust_signals(borrower_id)

    assert signals.book_care == "Needs Improvement"


def test_unrated_loans_are_ignored_for_book_care(db):
    owner_id = _make_user(db, "owner6@example.com")
    borrower_id = _make_user(db, "borrower6@example.com")
    book_a = _make_book(db, owner_id, "Rated Book")
    book_b = _make_book(db, owner_id, "Unrated Book")

    loan_a = loan_service.create_loan(
        book_id=book_a, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(
        loan_a.id, return_date=REFERENCE_DATE + dt.timedelta(days=14),
        condition_rating="better_than_before",
    )

    loan_b = loan_service.create_loan(
        book_id=book_b, borrower_id=borrower_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(loan_b.id, return_date=REFERENCE_DATE + dt.timedelta(days=14))  # no rating

    # Only the rated loan should count -> 100 -> Excellent, not averaged
    # down by the unrated one.
    signals = trust_service.get_trust_signals(borrower_id)

    assert signals.book_care == "Excellent"


def test_trust_service_has_no_reflex_dependency():
    with open(trust_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source