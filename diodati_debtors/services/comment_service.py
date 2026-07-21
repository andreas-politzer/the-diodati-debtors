"""Comment service — one comment system for every Post, regardless of
its context (club feed, board, or book discussion). Author-only
edit/delete, no moderation, per the Communication Domain Model.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import InvalidPostDataError, NotAuthorizedError, NotFoundError
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.comment import Comment
from ..models.post import Post
from ..models.user import User


@dataclass(frozen=True)
class CommentResult:
    id: int
    post_id: int
    author_id: int
    content: str
    created_at: dt.datetime

    def to_dict(self) -> dict:
        return asdict(self)


def _to_result(comment: Comment) -> CommentResult:
    return CommentResult(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        content=comment.content,
        created_at=comment.created_at,
    )


def create_comment(post_id: int, author_id: int, content: str) -> CommentResult:
    """Add a comment to a post.

    Raises:
        NotFoundError: if the post or author does not exist.
        InvalidPostDataError: if content is blank.
    """
    stripped_content = blank_to_none(content)
    if stripped_content is None:
        raise InvalidPostDataError("Comment content must not be blank.")

    with get_session() as session:
        post = session.get(Post, post_id)
        if post is None:
            raise NotFoundError(f"Post {post_id} does not exist.")
        author = session.get(User, author_id)
        if author is None:
            raise NotFoundError(f"User {author_id} does not exist.")

        comment = Comment(post_id=post_id, author_id=author_id, content=stripped_content)
        session.add(comment)
        session.flush()
        return _to_result(comment)


def list_comments_for_post(post_id: int) -> list[CommentResult]:
    """Oldest first — comments read like a conversation, not a feed."""
    with get_session() as session:
        comments = session.scalars(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at)
        ).all()
        return [_to_result(c) for c in comments]


def delete_comment(comment_id: int, author_id: int) -> None:
    """Author-only.

    Raises:
        NotFoundError: if the comment does not exist.
        NotAuthorizedError: if author_id isn't the comment's author.
    """
    with get_session() as session:
        comment = session.get(Comment, comment_id)
        if comment is None:
            raise NotFoundError(f"Comment {comment_id} does not exist.")
        if comment.author_id != author_id:
            raise NotAuthorizedError(
                f"User {author_id} is not the author of comment {comment_id}."
            )
        session.delete(comment)
        session.flush()


__all__ = ["CommentResult", "create_comment", "list_comments_for_post", "delete_comment"]