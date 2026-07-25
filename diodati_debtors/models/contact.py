"""Contact entity — a personal, non-registered borrower (e.g. a
neighbour, grandmother, family member with no account). Private to its
owner, never shared, never globally searchable — see the "People are
people, mates are mates" architecture note (project vault): unified
with club members at the navigation/mental-model level only, never on
the service/data level.

Never deletable once it has loan history, same philosophy as Book/Loan
(no delete function exists — only create/update).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    owner: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<Contact id={self.id} name={self.name!r}>"


__all__ = ["Contact"]