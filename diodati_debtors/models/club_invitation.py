"""ClubInvitation — a full domain concept for inviting someone to
join a club, independent of HOW the invitation is delivered (email
today, potentially other channels later — same "domain vs. adapter"
separation as Borrowing Inquiry uses Gemini/Google Books).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class ClubInvitation(Base):
    __tablename__ = "club_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False, index=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invited_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    group: Mapped["Group"] = relationship()
    inviter: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<ClubInvitation group_id={self.group_id} invited_email={self.invited_email!r}>"


__all__ = ["ClubInvitation"]