"""LoanRequest entity — a request to borrow a book.

Separate business concept from Loan per the Domain Model v2 decision
(project vault): a request may be declined, cancelled, or expire
without ever becoming a Loan. Replaces the previous instant "Lend to"
flow — the owner must approve before a Loan is created. Approved
requests are never deleted — same immutable-history principle as Loan
itself.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base
from .enums import RequestStatus


class LoanRequest(Base):
    __tablename__ = "loan_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=False, index=True
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, native_enum=False, length=20, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=RequestStatus.PENDING,
        nullable=False,
    )
    requested_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    book: Mapped["Book"] = relationship()
    requester: Mapped["User"] = relationship(foreign_keys=[requester_id])
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<LoanRequest book_id={self.book_id} requester_id={self.requester_id} status={self.status}>"


__all__ = ["LoanRequest"]