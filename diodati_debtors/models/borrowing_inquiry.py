"""BorrowingInquiry — the "Public Borrowing Inquiry" process from the
Personal Messages domain session (project vault): a book-bound
conversation between two users who are NOT necessarily connected
through a shared club, triggered only via the Librarian's mediation
when a book explicitly allows public enquiries.

Kept entirely separate from LoanRequest (which requires club
membership) and from ClubConversation (which requires no book at
all) — different fachlich processes, not variants of one generic
"conversation" concept.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base
from .enums import InquiryStatus


class BorrowingInquiry(Base):
    __tablename__ = "borrowing_inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=False, index=True
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    status: Mapped[InquiryStatus] = mapped_column(
        Enum(
            InquiryStatus,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=InquiryStatus.OPEN,
        nullable=False,
    )

    book: Mapped["Book"] = relationship()
    requester: Mapped["User"] = relationship(foreign_keys=[requester_id])
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    messages: Mapped[list["BorrowingInquiryMessage"]] = relationship(
        back_populates="inquiry", cascade="all, delete-orphan",
        order_by="BorrowingInquiryMessage.sent_at",
    )

    def __repr__(self) -> str:
        return f"<BorrowingInquiry id={self.id} book_id={self.book_id}>"


class BorrowingInquiryMessage(Base):
    __tablename__ = "borrowing_inquiry_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(
        ForeignKey("borrowing_inquiries.id"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    inquiry: Mapped["BorrowingInquiry"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<BorrowingInquiryMessage id={self.id} inquiry_id={self.inquiry_id}>"


__all__ = ["BorrowingInquiry", "BorrowingInquiryMessage"]