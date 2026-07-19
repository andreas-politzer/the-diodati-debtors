"""User entity.

Design note: one User row per person, even if they belong to multiple
groups (see GroupMembership) — this is what makes the Kicktipp-style
"one password, pick a club after login" flow possible.

Email normalization (lowercase, trimmed) is a service-layer concern
(auth_service), not enforced here — this model stores exactly what it
is given. Uniqueness is enforced at the database level only.

Timestamps: see core/time.py for the project-wide UTC policy.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Intentionally not unique — a display label, not an identity.
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    memberships: Mapped[list["GroupMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    books: Mapped[list["Book"]] = relationship(back_populates="owner")
    loans: Mapped[list["Loan"]] = relationship(back_populates="borrower")
    posts: Mapped[list["Post"]] = relationship(back_populates="author")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"