"""Read-tracking service — PostRead/CommentRead, per the 02.08.
architecture decision (project vault): read status follows the
fachlich entity (Post, Comment), not the UI projection (Global Board
vs. Club Feed). A new comment never makes its parent post unread
again — two fully independent read states.

Per the 06.08. Baseline architecture decision (project vault): a
user's feed_baseline_at (set once at account creation, backfilled to
migration-time for existing users) means posts/comments created
BEFORE that timestamp never count as unread — not because they're
marked as read, but because they simply predate this user's presence
in the community. No mass PostRead/CommentRead rows are created for
historical content; the baseline is checked directly against
Post.created_at/Comment.created_at instead.
"""

from __future__ import annotations

from sqlalchemy import func, select

from ..db.session import get_session
from ..models.comment import Comment
from ..models.post import Post
from ..models.post_read import CommentRead, PostRead
from ..models.user import User


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
    yet read AND that were created at/after their feed_baseline_at."""
    if not post_ids:
        return set()
    with get_session() as session:
        user = session.get(User, user_id)
        baseline = user.feed_baseline_at if user else None

        posts_after_baseline = set(post_ids)
        if baseline is not None:
            posts_after_baseline = set(
                session.scalars(
                    select(Post.id).where(Post.id.in_(post_ids), Post.created_at >= baseline)
                ).all()
            )

        read_ids = session.scalars(
            select(PostRead.post_id).where(
                PostRead.user_id == user_id, PostRead.post_id.in_(post_ids)
            )
        ).all()
        read_id_set = set(read_ids)
        return {pid for pid in posts_after_baseline if pid not in read_id_set}


def get_unread_comment_ids(user_id: int, comment_ids: list[int]) -> set[int]:
    """Given a list of comment IDs, returns the subset the user has
    NOT yet read AND that were created at/after their feed_baseline_at."""
    if not comment_ids:
        return set()
    with get_session() as session:
        user = session.get(User, user_id)
        baseline = user.feed_baseline_at if user else None

        comments_after_baseline = set(comment_ids)
        if baseline is not None:
            comments_after_baseline = set(
                session.scalars(
                    select(Comment.id).where(
                        Comment.id.in_(comment_ids), Comment.created_at >= baseline
                    )
                ).all()
            )

        read_ids = session.scalars(
            select(CommentRead.comment_id).where(
                CommentRead.user_id == user_id, CommentRead.comment_id.in_(comment_ids)
            )
        ).all()
        read_id_set = set(read_ids)
        return {cid for cid in comments_after_baseline if cid not in read_id_set}


def count_unread_global_posts(user_id: int) -> int:
    """Counts unread posts in the Global Board (group_id IS NULL,
    book_id IS NULL) for this user, created at/after their
    feed_baseline_at — a direct, efficient count, not "load
    everything, then measure the list."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return 0
        baseline = user.feed_baseline_at

        total = session.scalar(
            select(func.count(Post.id)).where(
                Post.group_id.is_(None),
                Post.book_id.is_(None),
                Post.created_at >= baseline,
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
                Post.created_at >= baseline,
            )
        )
        return total - (read_count or 0)


def count_unread_club_posts(user_id: int, group_id: int) -> int:
    """Counts unread posts in a specific club's feed for this user,
    created at/after their feed_baseline_at."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return 0
        baseline = user.feed_baseline_at

        total = session.scalar(
            select(func.count(Post.id)).where(
                Post.group_id == group_id, Post.created_at >= baseline
            )
        )
        if not total:
            return 0
        read_count = session.scalar(
            select(func.count(PostRead.id))
            .join(Post, Post.id == PostRead.post_id)
            .where(
                PostRead.user_id == user_id,
                Post.group_id == group_id,
                Post.created_at >= baseline,
            )
        )
        return total - (read_count or 0)


__all__ = [
    "mark_post_read",
    "mark_comment_read",
    "get_unread_post_ids",
    "get_unread_comment_ids",
    "count_unread_global_posts",
    "count_unread_club_posts",
]