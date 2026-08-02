"""PostRead / CommentRead — read-tracking for the shared Post/Comment
entities (Global Board, Club Feed, Book Discussion). Follows the
fachlich entity (Post, Comment), not the UI projection (Global Board
vs. Club Feed are the same underlying Post table) — per the 02.08.
architecture decision (project vault).

A new comment on an already-read post does NOT make the post unread
again — these are two independent read states, not one cascading
status. The Dashboard-level unread count only considers PostRead
(new posts), never CommentRead — comments are surfaced one level
down, on the feed page itself, not in the top-level badge (Andy's
explicit decision, 02.08.).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class PostRead(Base):
    __tablename__ = "post_reads"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_post_read_user_post"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False, index=True)
    read_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped["User"] = relationship()
    post: Mapped["Post"] = relationship()

    def __repr__(self) -> str:
        return f"<PostRead user_id={self.user_id} post_id={self.post_id}>"


class CommentRead(Base):
    __tablename__ = "comment_reads"
    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="uq_comment_read_user_comment"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False, index=True)
    read_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped["User"] = relationship()
    comment: Mapped["Comment"] = relationship()

    def __repr__(self) -> str:
        return f"<CommentRead user_id={self.user_id} comment_id={self.comment_id}>"


__all__ = ["PostRead", "CommentRead"]