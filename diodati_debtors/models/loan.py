"""Loan entity.

A Loan links exactly one Book to one borrowing User, with a loan date,
a due date, and an optional return date. `return_date IS NULL` means
the loan is currently active.

The rule "a book may not have two active loans at once" is NOT enforced
here — MySQL has no partial unique index, and business rules live in
the service layer per the Architecture Contract. This model only
describes the shape of a loan record.

No cascade toward Book/User: a Loan is historical business record, not
a dependent row — see Struktur.md, Loan-History-Policy (open decision
on delete behaviour, deferred until service layer exists).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

from .enums import ConditionRating


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=False, index=True
    )
    borrower_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    loan_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    return_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    condition_rating: Mapped["ConditionRating | None"] = mapped_column(
        Enum(
            ConditionRating,
            native_enum=False,
            length=25,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=True,
    )

    book: Mapped["Book"] = relationship(back_populates="loans")
    borrower: Mapped["User"] = relationship(back_populates="loans")

    @property
    def is_active(self) -> bool:
        """Convenience accessor describing current state — not an
        enforcement point. Whether a NEW active loan may be created is
        decided exclusively by loan_service, never by this property.
        """
        return self.return_date is None

    def __repr__(self) -> str:
        return f"<Loan id={self.id} book_id={self.book_id} active={self.is_active}>"
    
