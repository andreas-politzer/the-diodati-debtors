"""Book entity.

Phase 2 scope: manual fields only (title, author, isbn as plain text).
Open Library ISBN lookup is deferred — isbn here is just a string field,
not yet validated or auto-populated.

location (free text, e.g. "Living room, green shelf", "Basement",
"Box 3") — a practical feature per Domain Model v2, not a technical
constraint. Optional, no fixed vocabulary.

No cascade toward Loan: deleting a book with historical loan records is
a domain-policy decision to be reviewed once the full model exists (see
Struktur.md / Codex review notes), not an automatic DB behaviour.

Timestamps: see core/time.py for the project-wide UTC policy.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="books")
    loans: Mapped[list["Loan"]] = relationship(back_populates="book")

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r}>"