"""Book entity.

Phase 2 scope: manual fields only (title, author, isbn as plain text).
Open Library ISBN lookup exists now (book_service.lookup_isbn) —
isbn/title/author here remain plain fields, populated either manually
or via the lookup, no separate representation.

location (free text) — a practical feature, not a technical constraint.

genre (optional, single value from BookGenre) — a flat, pragmatic
browsing vocabulary, not academic taxonomy. Deliberately single-value
in V1; see Domain Model v2 for the reasoning and the future migration
path to many-to-many, if ever needed.

No cascade toward Loan: deleting a book with historical loan records
is blocked at the service layer (book_service.delete_book), not by a
database cascade.

Timestamps: see core/time.py for the project-wide UTC policy.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base
from .enums import BookGenre


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
    genre: Mapped[BookGenre | None] = mapped_column(
        Enum(
            BookGenre,
            native_enum=False,
            length=30,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=True,
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="books")
    loans: Mapped[list["Loan"]] = relationship(back_populates="book")

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r}>"