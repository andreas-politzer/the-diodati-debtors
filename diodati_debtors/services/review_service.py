"""Review service — exactly one review per user per book (create-or-
update, not versioned). Only the book's owner or anyone who has ever
borrowed it (active or historical loan) may review — real reading
experience implied, not just visibility.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import (
    InvalidReviewDataError,
    NotAuthorizedError,
    NotEligibleToReviewError,
    NotFoundError,
)
from ..core.normalize import blank_to_none
from ..core.time import utcnow
from ..db.session import get_session
from ..models.book import Book
from ..models.loan import Loan
from ..models.review import Review
from ..models.user import User

MIN_RATING = 1
MAX_RATING = 5


@dataclass(frozen=True)
class ReviewResult:
    id: int
    book_id: int
    user_id: int
    rating: int
    content: str
    created_at: dt.datetime
    updated_at: dt.datetime

    def to_dict(self) -> dict:
        return asdict(self)


def _to_result(review: Review) -> ReviewResult:
    return ReviewResult(
        id=review.id,
        book_id=review.book_id,
        user_id=review.user_id,
        rating=review.rating,
        content=review.content,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def _is_eligible(session, book: Book, user_id: int) -> bool:
    if book.owner_id == user_id:
        return True
    return (
        session.scalar(
            select(Loan).where(Loan.book_id == book.id, Loan.borrower_id == user_id)
        )
        is not None
    )


def submit_review(book_id: int, user_id: int, rating: int, content: str) -> ReviewResult:
    """Create or update this user's review for this book.

    Raises:
        NotFoundError: if the book or user does not exist.
        NotEligibleToReviewError: if the user has neither owned nor
            ever borrowed the book.
        InvalidReviewDataError: if rating is out of range or content
            is blank.
    """
    if not MIN_RATING <= rating <= MAX_RATING:
        raise InvalidReviewDataError(
            f"Rating must be between {MIN_RATING} and {MAX_RATING}."
        )
    stripped_content = blank_to_none(content)
    if stripped_content is None:
        raise InvalidReviewDataError("Review content must not be blank.")

    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")
        user = session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} does not exist.")

        if not _is_eligible(session, book, user_id):
            raise NotEligibleToReviewError(
                f"User {user_id} has never owned or borrowed book {book_id}."
            )

        existing = session.scalar(
            select(Review).where(Review.book_id == book_id, Review.user_id == user_id)
        )
        if existing is not None:
            existing.rating = rating
            existing.content = stripped_content
            existing.updated_at = utcnow()
            session.flush()
            return _to_result(existing)

        review = Review(
            book_id=book_id, user_id=user_id, rating=rating, content=stripped_content
        )
        session.add(review)
        session.flush()
        return _to_result(review)


def list_reviews_for_book(book_id: int) -> list[ReviewResult]:
    """Most recent first."""
    with get_session() as session:
        reviews = session.scalars(
            select(Review).where(Review.book_id == book_id).order_by(Review.created_at.desc())
        ).all()
        return [_to_result(r) for r in reviews]


def delete_review(review_id: int, user_id: int) -> None:
    """Author-only.

    Raises:
        NotFoundError: if the review does not exist.
        NotAuthorizedError: if user_id isn't the review's author.
    """
    with get_session() as session:
        review = session.get(Review, review_id)
        if review is None:
            raise NotFoundError(f"Review {review_id} does not exist.")
        if review.user_id != user_id:
            raise NotAuthorizedError(f"User {user_id} is not the author of review {review_id}.")
        session.delete(review)
        session.flush()


__all__ = [
    "ReviewResult",
    "MIN_RATING",
    "MAX_RATING",
    "submit_review",
    "list_reviews_for_book",
    "delete_review",
]