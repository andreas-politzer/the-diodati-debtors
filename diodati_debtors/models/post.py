"""Post entity — Discussion, Club Post, and Community Board are all
the same entity, distinguished only by context (Communication Domain
Model, project vault):

- book_id set   → the post is about a specific book ("Discussion")
- group_id set  → club-internal; group_id NULL → global Board
- post_type is purely presentational (icon/color/filter), never
  changes the lifecycle

Posts are immutable except by their own author (edit/delete — no
moderation, no founder overrides, per the Communication Domain Model
decision). No updated_at — see below.

Feed ordering must always use ORDER BY created_at at the database
level, never ORM insertion order.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base
from .enums import PostType


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"), nullable=True, index=True
    )
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey("books.id"), nullable=True, index=True
    )
    post_type: Mapped[PostType] = mapped_column(
        Enum(
            PostType,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=PostType.GENERAL,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    author: Mapped["User"] = relationship(back_populates="posts")
    group: Mapped["Group | None"] = relationship(back_populates="posts")
    book: Mapped["Book | None"] = relationship()
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} author_id={self.author_id}>"