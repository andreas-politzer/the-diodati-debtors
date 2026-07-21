"""Post service — one entity, three projections (Communication Domain
Model, project vault): Club Feed, Global Board, Book Discussion are
the same Post table, filtered differently, never separate tables.

Visibility follows existing rules, no new permission system:
- Global Board: any authenticated user
- Club Feed: only members of that group
- Book Discussion: only users who can see that book (members of any
  group the book's owner belongs to, plus the owner)

Editing/deleting: author-only, no moderation, no founder overrides
(per the Communication Domain Model decision).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import (
    InvalidPostDataError,
    NotAuthorizedError,
    NotAuthorizedToPostError,
    NotFoundError,
)
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.book import Book
from ..models.enums import PostType
from ..models.group import GroupMembership
from ..models.post import Post
from ..models.user import User


@dataclass(frozen=True)
class PostResult:
    id: int
    author_id: int
    group_id: int | None
    book_id: int | None
    post_type: str
    content: str
    created_at: dt.datetime

    def to_dict(self) -> dict:
        return asdict(self)


def _to_result(post: Post) -> PostResult:
    return PostResult(
        id=post.id,
        author_id=post.author_id,
        group_id=post.group_id,
        book_id=post.book_id,
        post_type=post.post_type.value,
        content=post.content,
        created_at=post.created_at,
    )


def _is_group_member(session, user_id: int, group_id: int) -> bool:
    return (
        session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == user_id,
                GroupMembership.group_id == group_id,
            )
        )
        is not None
    )


def _can_view_book(session, user_id: int, book: Book) -> bool:
    """Same visibility rule as the rest of the app: the book's owner,
    or anyone in a group the owner belongs to.
    """
    if book.owner_id == user_id:
        return True
    owner_group_ids = {
        m.group_id
        for m in session.scalars(
            select(GroupMembership).where(GroupMembership.user_id == book.owner_id)
        ).all()
    }
    if not owner_group_ids:
        return False
    return (
        session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == user_id,
                GroupMembership.group_id.in_(owner_group_ids),
            )
        )
        is not None
    )


def create_post(
    author_id: int,
    content: str,
    group_id: int | None = None,
    book_id: int | None = None,
    post_type: str = PostType.GENERAL.value,
) -> PostResult:
    """Create a post — Club Feed (group_id set), Global Board (both
    None), or Book Discussion (book_id set).

    Raises:
        NotFoundError: if author/group/book doesn't exist.
        InvalidPostDataError: if content is blank.
        NotAuthorizedToPostError: if the author can't see the target
            club/book.
    """
    stripped_content = blank_to_none(content)
    if stripped_content is None:
        raise InvalidPostDataError("Post content must not be blank.")

    with get_session() as session:
        author = session.get(User, author_id)
        if author is None:
            raise NotFoundError(f"User {author_id} does not exist.")

        if group_id is not None:
            from ..models.group import Group

            group = session.get(Group, group_id)
            if group is None:
                raise NotFoundError(f"Group {group_id} does not exist.")
            if not _is_group_member(session, author_id, group_id):
                raise NotAuthorizedToPostError(
                    f"User {author_id} is not a member of group {group_id}."
                )

        if book_id is not None:
            book = session.get(Book, book_id)
            if book is None:
                raise NotFoundError(f"Book {book_id} does not exist.")
            if not _can_view_book(session, author_id, book):
                raise NotAuthorizedToPostError(
                    f"User {author_id} cannot view book {book_id}."
                )

        post = Post(
            author_id=author_id,
            group_id=group_id,
            book_id=book_id,
            post_type=PostType(post_type),
            content=stripped_content,
        )
        session.add(post)
        session.flush()
        return _to_result(post)


def list_global_board_posts() -> list[PostResult]:
    """Global Board — no group, no book, most recent first."""
    with get_session() as session:
        posts = session.scalars(
            select(Post)
            .where(Post.group_id.is_(None), Post.book_id.is_(None))
            .order_by(Post.created_at.desc())
        ).all()
        return [_to_result(p) for p in posts]


def list_club_feed_posts(group_id: int) -> list[PostResult]:
    """Club Feed — posts belonging to this group, most recent first."""
    with get_session() as session:
        posts = session.scalars(
            select(Post)
            .where(Post.group_id == group_id)
            .order_by(Post.created_at.desc())
        ).all()
        return [_to_result(p) for p in posts]


def list_book_discussion_posts(book_id: int) -> list[PostResult]:
    """Book Discussion — posts about this specific book, most recent first."""
    with get_session() as session:
        posts = session.scalars(
            select(Post)
            .where(Post.book_id == book_id)
            .order_by(Post.created_at.desc())
        ).all()
        return [_to_result(p) for p in posts]


def delete_post(post_id: int, author_id: int) -> None:
    """Author-only. No moderation, no founder override.

    Raises:
        NotFoundError: if the post does not exist.
        NotAuthorizedError: if author_id isn't the post's author.
    """
    with get_session() as session:
        post = session.get(Post, post_id)
        if post is None:
            raise NotFoundError(f"Post {post_id} does not exist.")
        if post.author_id != author_id:
            raise NotAuthorizedError(
                f"User {author_id} is not the author of post {post_id}."
            )
        session.delete(post)
        session.flush()


__all__ = [
    "PostResult",
    "create_post",
    "list_global_board_posts",
    "list_club_feed_posts",
    "list_book_discussion_posts",
    "delete_post",
]