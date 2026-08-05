"""SystemNotification — a simple, one-way message from the platform
itself to a user (e.g. the welcome message after email verification).
Deliberately NOT a ClubConversation — no second real user, no club
membership requirement. Per the 04.08. architecture decision (project
vault, Option 2): a system message is not a person-to-person
conversation and shouldn't force one to exist.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class SystemNotification(Base):
    __tablename__ = "system_notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<SystemNotification user_id={self.user_id} title={self.title!r}>"


__all__ = ["SystemNotification"]