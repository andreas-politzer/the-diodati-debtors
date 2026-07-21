"""Comment entity — belongs to exactly one Post, regardless of that
Post's context (club feed, global board, or book discussion — same
Post entity, different projections). One single comment system for
all of them, per the Communication Domain Model.

Editable/deletable only by their own author (no moderation yet, per
the Communication Domain Model decision).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<Comment id={self.id} post_id={self.post_id}>"