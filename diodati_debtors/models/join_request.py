"""JoinRequest entity — a request to join a group.

Separate business concept from GroupMembership per the Domain Model v2
decision (project vault): a membership can exist without ever having a
request (founder, admin adds member, invitation, data import), and a
request can end without ever becoming a membership (declined,
cancelled, expired). Approved requests are never deleted — same
immutable-history principle as Loan.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base
from .enums import RequestStatus


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False, index=True
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

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    group: Mapped["Group"] = relationship()
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<JoinRequest user_id={self.user_id} group_id={self.group_id} status={self.status}>"


__all__ = ["JoinRequest"]