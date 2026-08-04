"""EmailVerificationToken — a single-use, time-limited token proving
ownership of the email address used at registration. Per the 03.08.
architecture decision (project vault): email verification is pure
infrastructure, not a domain/trust concept — it confirms email
ownership only, nothing about identity or reliability.

A token is invalidated (used_at set) either when successfully used,
or implicitly superseded when a new token is generated via "resend" —
old tokens are never deleted, kept as an audit trail, same immutable-
history principle as Loan/LoanRequest.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<EmailVerificationToken user_id={self.user_id} used={self.used_at is not None}>"


__all__ = ["EmailVerificationToken"]