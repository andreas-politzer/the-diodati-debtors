"""Borrowing Inquiry service — the "Public Borrowing Inquiry" process
from the Personal Messages domain session (project vault): a
book-bound conversation between two users, triggered only via the
Librarian's mediation, requiring no shared club membership.

Domain rules (agreed 29./30.07., project vault):
- Exactly one OPEN inquiry per (book, requester) — not "ever only
  one", since a closed inquiry represents a natural conversational
  endpoint (declined, book already lent, requester lost interest),
  not a permanent restriction.
- The first message is not a special case — start_inquiry() creates
  the inquiry AND its first message together, in that order.
- Reading is a side effect of opening an inquiry, not a separate
  bulk operation — no "mark as read" as its own user action.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import (
    NotAuthorizedError,
    NotFoundError,
)
from ..db.session import get_session
from ..models.book import Book
from ..models.borrowing_inquiry import BorrowingInquiry, BorrowingInquiryMessage
from ..models.enums import BorrowingVisibility, InquiryStatus, ProfileVisibility
from ..models.user_profile import UserProfile
from ..models.user import User


class InquiryNotAllowedError(Exception):
    """Raised when a book/profile combination does not permit a
    Public Borrowing Inquiry (per borrowing_visibility + owner's
    profile visibility)."""


class DuplicateOpenInquiryError(Exception):
    """Raised when the requester already has an OPEN inquiry for
    this exact book — must be closed before a new one can start."""


@dataclass(frozen=True)
class MessageResult:
    id: int
    sender_id: int
    content: str
    sent_at: dt.datetime
    read_at: dt.datetime | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class InquiryResult:
    id: int
    book_id: int
    requester_id: int
    owner_id: int
    status: str
    created_at: dt.datetime
    messages: list[MessageResult]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "requester_id": self.requester_id,
            "owner_id": self.owner_id,
            "status": self.status,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages],
        }


def _to_message_result(message: BorrowingInquiryMessage) -> MessageResult:
    return MessageResult(
        id=message.id,
        sender_id=message.sender_id,
        content=message.content,
        sent_at=message.sent_at,
        read_at=message.read_at,
    )


def _to_inquiry_result(inquiry: BorrowingInquiry) -> InquiryResult:
    return InquiryResult(
        id=inquiry.id,
        book_id=inquiry.book_id,
        requester_id=inquiry.requester_id,
        owner_id=inquiry.owner_id,
        status=inquiry.status.value,
        created_at=inquiry.created_at,
        messages=[_to_message_result(m) for m in inquiry.messages],
    )


def start_inquiry(book_id: int, requester_id: int, message: str) -> InquiryResult:
    """Creates a new Public Borrowing Inquiry AND its first message
    together — the first message is not a special case appended
    later, it's part of the same act of starting the conversation.

    Raises:
        NotFoundError: if the book or requester does not exist.
        InquiryNotAllowedError: if the book's borrowing_visibility is
            not PUBLIC_ENQUIRIES_ALLOWED, or the owner's profile is
            PRIVATE.
        DuplicateOpenInquiryError: if the requester already has an
            OPEN inquiry for this exact book.
    """
    with get_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} does not exist.")

        requester = session.get(User, requester_id)
        if requester is None:
            raise NotFoundError(f"User {requester_id} does not exist.")

        if book.borrowing_visibility != BorrowingVisibility.PUBLIC_ENQUIRIES_ALLOWED:
            raise InquiryNotAllowedError(
                f"Book {book_id} does not allow public borrowing enquiries."
            )

        owner_profile = session.query(UserProfile).filter_by(user_id=book.owner_id).first()
        if owner_profile is not None and owner_profile.visibility == ProfileVisibility.PRIVATE:
            raise InquiryNotAllowedError(
                f"Owner of book {book_id} has set their profile to private."
            )

        existing_open = session.scalar(
            select(BorrowingInquiry).where(
                BorrowingInquiry.book_id == book_id,
                BorrowingInquiry.requester_id == requester_id,
                BorrowingInquiry.status == InquiryStatus.OPEN,
            )
        )
        if existing_open is not None:
            raise DuplicateOpenInquiryError(
                f"User {requester_id} already has an open inquiry for book {book_id}."
            )

        inquiry = BorrowingInquiry(
            book_id=book_id,
            requester_id=requester_id,
            owner_id=book.owner_id,
            status=InquiryStatus.OPEN,
        )
        session.add(inquiry)
        session.flush()

        first_message = BorrowingInquiryMessage(
            inquiry_id=inquiry.id,
            sender_id=requester_id,
            content=message,
        )
        session.add(first_message)
        session.flush()
        session.refresh(inquiry)

        return _to_inquiry_result(inquiry)


def reply(inquiry_id: int, sender_id: int, message: str) -> InquiryResult:
    """Adds a message to an existing inquiry. Either participant
    (requester or owner) may reply, as long as the inquiry is OPEN.

    Raises:
        NotFoundError: if the inquiry does not exist.
        NotAuthorizedError: if sender_id is neither the requester nor
            the owner of this inquiry.
        InquiryNotAllowedError: if the inquiry is already CLOSED.
    """
    with get_session() as session:
        inquiry = session.get(BorrowingInquiry, inquiry_id)
        if inquiry is None:
            raise NotFoundError(f"BorrowingInquiry {inquiry_id} does not exist.")

        if sender_id not in (inquiry.requester_id, inquiry.owner_id):
            raise NotAuthorizedError(
                f"User {sender_id} is not a participant in inquiry {inquiry_id}."
            )

        if inquiry.status != InquiryStatus.OPEN:
            raise InquiryNotAllowedError(
                f"Inquiry {inquiry_id} is closed and no longer accepts messages."
            )

        new_message = BorrowingInquiryMessage(
            inquiry_id=inquiry_id,
            sender_id=sender_id,
            content=message,
        )
        session.add(new_message)
        session.flush()
        session.refresh(inquiry)

        return _to_inquiry_result(inquiry)


def close_inquiry(inquiry_id: int, closer_id: int) -> InquiryResult:
    """Either participant may close an inquiry — the natural
    conversational endpoint (declined, book already lent, lost
    interest). Closing is never automatic; it's an explicit action.

    Raises:
        NotFoundError: if the inquiry does not exist.
        NotAuthorizedError: if closer_id is neither the requester nor
            the owner.
    """
    with get_session() as session:
        inquiry = session.get(BorrowingInquiry, inquiry_id)
        if inquiry is None:
            raise NotFoundError(f"BorrowingInquiry {inquiry_id} does not exist.")

        if closer_id not in (inquiry.requester_id, inquiry.owner_id):
            raise NotAuthorizedError(
                f"User {closer_id} is not a participant in inquiry {inquiry_id}."
            )

        inquiry.status = InquiryStatus.CLOSED
        session.flush()
        session.refresh(inquiry)

        return _to_inquiry_result(inquiry)


def list_inquiries_for_user(user_id: int) -> list[InquiryResult]:
    """All inquiries this user participates in — either as requester
    or as book owner — any status."""
    with get_session() as session:
        inquiries = session.scalars(
            select(BorrowingInquiry)
            .where(
                (BorrowingInquiry.requester_id == user_id)
                | (BorrowingInquiry.owner_id == user_id)
            )
            .order_by(BorrowingInquiry.created_at.desc())
        ).all()
        return [_to_inquiry_result(i) for i in inquiries]


def open_inquiry(inquiry_id: int, viewer_id: int) -> InquiryResult:
    """Opening an inquiry marks all messages directed AT the viewer
    as read — reading is a side effect of viewing, not a separate
    user action (per the domain session decision).

    Raises:
        NotFoundError: if the inquiry does not exist.
        NotAuthorizedError: if viewer_id is not a participant.
    """
    with get_session() as session:
        inquiry = session.get(BorrowingInquiry, inquiry_id)
        if inquiry is None:
            raise NotFoundError(f"BorrowingInquiry {inquiry_id} does not exist.")

        if viewer_id not in (inquiry.requester_id, inquiry.owner_id):
            raise NotAuthorizedError(
                f"User {viewer_id} is not a participant in inquiry {inquiry_id}."
            )

        now = dt.datetime.utcnow()
        for message in inquiry.messages:
            if message.sender_id != viewer_id and message.read_at is None:
                message.read_at = now

        session.flush()
        session.refresh(inquiry)

        return _to_inquiry_result(inquiry)


__all__ = [
    "MessageResult",
    "InquiryResult",
    "InquiryNotAllowedError",
    "DuplicateOpenInquiryError",
    "start_inquiry",
    "reply",
    "close_inquiry",
    "list_inquiries_for_user",
    "open_inquiry",
]