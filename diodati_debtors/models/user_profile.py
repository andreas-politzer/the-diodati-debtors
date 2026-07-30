"""UserProfile entity — the entirely optional, second layer described
in Personal Messages Domain Model.md (project vault): Account (User)
is mandatory (username/email/password), Profile is optional on top.

One shared visibility level for the whole profile (not per-field) —
a deliberate simplification agreed during the domain session, to keep
UI/data modeling effort proportionate. Controls both plattform-wide
Public Borrowing Inquiries AND club-internal messaging — one setting,
two consumers, not a separate "allow direct messages" toggle (that
would be the on-ramp to a general-purpose messenger, which this
project explicitly avoids).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base
from .enums import ProfileVisibility


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )

    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    favorite_genre: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    visibility: Mapped[ProfileVisibility] = mapped_column(
        Enum(
            ProfileVisibility,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=ProfileVisibility.CLUBS_ONLY,
        nullable=False,
    )

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} visibility={self.visibility}>"


__all__ = ["UserProfile"]