"""Tests for review_service: eligibility (owner/borrower only),
create-or-update semantics, rating bounds, author-only deletion.
"""

from __future__ import annotations

import datetime as dt

import pytest

from diodati_debtors.core.exceptions import (
    InvalidReviewDataError,
    NotAuthorizedError,
    NotEligibleToReviewError,
    NotFoundError,
)
from diodati_debtors.models.user import User
from diodati_debtors.services import book_service, loan_service, review_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_owner_can_submit_review(db):
    owner_id = _make_user(db, "owner1@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Frankenstein")

    result = review_service.submit_review(
        book_id=book.id, user_id=owner_id, rating=5, content="A masterpiece."
    )

    assert result.rating == 5


def test_former_borrower_can_submit_review(db):
    owner_id = _make_user(db, "owner2@example.com")
    borrower_id = _make_user(db, "borrower1@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Dracula")
    loan = loan_service.create_loan(
        book_id=book.id, borrower_id=borrower_id, due_date=dt.date.today() + dt.timedelta(days=14)
    )
    loan_service.return_loan(loan.id)

    result = review_service.submit_review(
        book_id=book.id, user_id=borrower_id, rating=4, content="Enjoyed it."
    )

    assert result.rating == 4


def test_outsider_cannot_submit_review(db):
    owner_id = _make_user(db, "owner3@example.com")
    outsider_id = _make_user(db, "outsider1@example.com")
    book = book_service.create_book(owner_id=owner_id, title="The Monk")

    with pytest.raises(NotEligibleToReviewError):
        review_service.submit_review(
            book_id=book.id, user_id=outsider_id, rating=3, content="Never read it."
        )


def test_submit_review_rejects_rating_out_of_range(db):
    owner_id = _make_user(db, "owner4@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Vathek")

    with pytest.raises(InvalidReviewDataError):
        review_service.submit_review(book_id=book.id, user_id=owner_id, rating=6, content="Too high")


def test_submit_review_rejects_blank_content(db):
    owner_id = _make_user(db, "owner5@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Melmoth")

    with pytest.raises(InvalidReviewDataError):
        review_service.submit_review(book_id=book.id, user_id=owner_id, rating=3, content="   ")


def test_second_submit_updates_existing_review(db):
    owner_id = _make_user(db, "owner6@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Zofloya")

    first = review_service.submit_review(
        book_id=book.id, user_id=owner_id, rating=2, content="First impression."
    )
    second = review_service.submit_review(
        book_id=book.id, user_id=owner_id, rating=5, content="Changed my mind, loved it."
    )

    assert first.id == second.id
    reviews = review_service.list_reviews_for_book(book.id)
    assert len(reviews) == 1
    assert reviews[0].rating == 5


def test_delete_review_succeeds_for_author(db):
    owner_id = _make_user(db, "owner7@example.com")
    book = book_service.create_book(owner_id=owner_id, title="The Italian")
    review = review_service.submit_review(book_id=book.id, user_id=owner_id, rating=4, content="Good")

    review_service.delete_review(review.id, user_id=owner_id)

    assert review_service.list_reviews_for_book(book.id) == []


def test_delete_review_rejects_non_author(db):
    owner_id = _make_user(db, "owner8@example.com")
    outsider_id = _make_user(db, "outsider2@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Uncle Silas")
    review = review_service.submit_review(book_id=book.id, user_id=owner_id, rating=3, content="OK")

    with pytest.raises(NotAuthorizedError):
        review_service.delete_review(review.id, user_id=outsider_id)


def test_review_service_has_no_reflex_dependency():
    with open(review_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source