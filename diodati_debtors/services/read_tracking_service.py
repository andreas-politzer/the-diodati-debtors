"""Read-tracking service — PostRead/CommentRead, per the 02.08.
architecture decision (project vault): read status follows the
fachlich entity (Post, Comment), not the UI projection (Global Board
vs. Club Feed). A new comment never makes its parent post unread
again — two fully independent read states.
"""

from __future__ import annotations

from sqlalchemy import select

from ..db.session import get_session
from ..models.post_read import CommentRead, PostRead


def mark_post_read(post_id: int, user_id: int) -> None:
    """Idempotent — marking an already-read post again is a no-op,
    never an error."""
    with get_session() as session:
        existing = session.scalar(
            select(PostRead).where(PostRead.user_id == user_id, PostRead.post_id == post_id)
        )
        if existing is not None:
            return
        session.add(PostRead(user_id=user_id, post_id=post_id))
        session.flush()


def mark_comment_read(comment_id: int, user_id: int) -> None:
    with get_session() as session:
        existing = session.scalar(
            select(CommentRead).where(
                CommentRead.user_id == user_id, CommentRead.comment_id == comment_id
            )
        )
        if existing is not None:
            return
        session.add(CommentRead(user_id=user_id, comment_id=comment_id))
        session.flush()


def get_unread_post_ids(user_id: int, post_ids: list[int]) -> set[int]:
    """Given a list of post IDs, returns the subset the user has NOT
    yet read."""
    if not post_ids:
        return set()
    with get_session() as session:
        read_ids = session.scalars(
            select(PostRead.post_id).where(
                PostRead.user_id == user_id, PostRead.post_id.in_(post_ids)
            )
        ).all()
        read_id_set = set(read_ids)
        return {pid for pid in post_ids if pid not in read_id_set}


def get_unread_comment_ids(user_id: int, comment_ids: list[int]) -> set[int]:
    """Given a list of comment IDs, returns the subset the user has
    NOT yet read."""
    if not comment_ids:
        return set()
    with get_session() as session:
        read_ids = session.scalars(
            select(CommentRead.comment_id).where(
                CommentRead.user_id == user_id, CommentRead.comment_id.in_(comment_ids)
            )
        ).all()
        read_id_set = set(read_ids)
        return {cid for cid in comment_ids if cid not in read_id_set}


__all__ = [
    "mark_post_read",
    "mark_comment_read",
    "get_unread_post_ids",
    "get_unread_comment_ids",
]