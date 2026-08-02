"""Read-tracking service — PostRead/CommentRead, per the 02.08.
architecture decision (project vault): read status follows the
fachlich entity (Post, Comment), not the UI projection (Global Board
vs. Club Feed). A new comment never makes its parent post unread
again — two fully independent read states.
"""

from __future__ import annotations

from sqlalchemy import func, select

from ..db.session import get_session
from ..models.post_read import CommentRead, PostRead
from ..models.post import Post


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

def count_unread_global_posts(user_id: int) -> int:
    """Counts unread posts in the Global Board (group_id IS NULL,
    book_id IS NULL) for this user — a direct, efficient count, not
    "load everything, then measure the list.""" 
    with get_session() as session:
        total = session.scalar(
            select(func.count(Post.id)).where(
                Post.group_id.is_(None), Post.book_id.is_(None)
            )
        )
        if not total:
            return 0
        read_count = session.scalar(
            select(func.count(PostRead.id))
            .join(Post, Post.id == PostRead.post_id)
            .where(
                PostRead.user_id == user_id,
                Post.group_id.is_(None),
                Post.book_id.is_(None),
            )
        )
        return total - (read_count or 0)


def count_unread_club_posts(user_id: int, group_id: int) -> int:
    """Counts unread posts in a specific club's feed for this user."""
    with get_session() as session:
        total = session.scalar(
            select(func.count(Post.id)).where(Post.group_id == group_id)
        )
        if not total:
            return 0
        read_count = session.scalar(
            select(func.count(PostRead.id))
            .join(Post, Post.id == PostRead.post_id)
            .where(PostRead.user_id == user_id, Post.group_id == group_id)
        )
        return total - (read_count or 0)


__all__ = [
    "mark_post_read",
    "mark_comment_read",
    "get_unread_post_ids",
    "get_unread_comment_ids",
]