"""Tests for post_service: the single Post entity across three
projections (Global Board, Club Feed, Book Discussion), visibility
rules, author-only deletion.
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import (
    InvalidPostDataError,
    NotAuthorizedError,
    NotAuthorizedToPostError,
    NotFoundError,
)
from diodati_debtors.models.enums import PostType
from diodati_debtors.models.group import Group, GroupMembership
from diodati_debtors.models.user import User
from diodati_debtors.services import book_service, post_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_group(db, name: str, founder_id: int) -> int:
    from diodati_debtors.services import group_service

    return group_service.create_group(founder_id=founder_id, name=name).id


def _add_membership(db, user_id: int, group_id: int) -> None:
    with db() as session:
        session.add(GroupMembership(user_id=user_id, group_id=group_id))
        session.commit()


def test_create_global_board_post_succeeds(db):
    author_id = _make_user(db, "author1@example.com")

    result = post_service.create_post(
        author_id=author_id, content="Anyone know a bookshop in Buxtehude?"
    )

    assert result.group_id is None
    assert result.book_id is None
    assert result.post_type == PostType.GENERAL.value


def test_create_post_rejects_blank_content(db):
    author_id = _make_user(db, "author2@example.com")

    with pytest.raises(InvalidPostDataError):
        post_service.create_post(author_id=author_id, content="   ")


def test_create_club_post_requires_membership(db):
    founder_id = _make_user(db, "founder1@example.com")
    outsider_id = _make_user(db, "outsider1@example.com")
    group_id = _make_group(db, "Gothic Novel Society", founder_id=founder_id)

    with pytest.raises(NotAuthorizedToPostError):
        post_service.create_post(
            author_id=outsider_id, content="Can I post here?", group_id=group_id
        )


def test_create_club_post_succeeds_for_member(db):
    founder_id = _make_user(db, "founder2@example.com")
    group_id = _make_group(db, "Gothic Novel Society", founder_id=founder_id)

    result = post_service.create_post(
        author_id=founder_id,
        content="Next meeting is Thursday.",
        group_id=group_id,
        post_type=PostType.ANNOUNCEMENT.value,
    )

    assert result.group_id == group_id
    assert result.post_type == PostType.ANNOUNCEMENT.value


def test_create_book_discussion_requires_visibility(db):
    owner_id = _make_user(db, "owner1@example.com")
    outsider_id = _make_user(db, "outsider2@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Frankenstein")

    with pytest.raises(NotAuthorizedToPostError):
        post_service.create_post(
            author_id=outsider_id, content="Great book!", book_id=book.id
        )


def test_create_book_discussion_succeeds_for_owner(db):
    owner_id = _make_user(db, "owner2@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Dracula")

    result = post_service.create_post(
        author_id=owner_id, content="My favorite gothic novel.", book_id=book.id
    )

    assert result.book_id == book.id


def test_create_book_discussion_succeeds_for_fellow_club_member(db):
    owner_id = _make_user(db, "owner3@example.com")
    member_id = _make_user(db, "member1@example.com")
    group_id = _make_group(db, "Shared Club", founder_id=owner_id)
    _add_membership(db, member_id, group_id)
    book = book_service.create_book(owner_id=owner_id, title="The Monk")

    result = post_service.create_post(
        author_id=member_id, content="Has anyone read this?", book_id=book.id
    )

    assert result.book_id == book.id


def test_list_global_board_posts_excludes_club_and_book_posts(db):
    founder_id = _make_user(db, "founder3@example.com")
    group_id = _make_group(db, "Some Club", founder_id=founder_id)
    book = book_service.create_book(owner_id=founder_id, title="Some Book")

    board_post = post_service.create_post(author_id=founder_id, content="Board post")
    post_service.create_post(author_id=founder_id, content="Club post", group_id=group_id)
    post_service.create_post(author_id=founder_id, content="Book post", book_id=book.id)

    results = post_service.list_global_board_posts()

    assert [r.id for r in results] == [board_post.id]


def test_list_club_feed_posts_returns_only_that_clubs_posts(db):
    founder_id = _make_user(db, "founder4@example.com")
    group_a = _make_group(db, "Club A", founder_id=founder_id)
    group_b = _make_group(db, "Club B", founder_id=founder_id)

    post_a = post_service.create_post(author_id=founder_id, content="In A", group_id=group_a)
    post_service.create_post(author_id=founder_id, content="In B", group_id=group_b)

    results = post_service.list_club_feed_posts(group_a)

    assert [r.id for r in results] == [post_a.id]


def test_delete_post_succeeds_for_author(db):
    author_id = _make_user(db, "author3@example.com")
    post = post_service.create_post(author_id=author_id, content="Delete me")

    post_service.delete_post(post.id, author_id=author_id)

   
    results = post_service.list_global_board_posts()
    assert results == []


def test_delete_post_rejects_non_author(db):
    author_id = _make_user(db, "author4@example.com")
    outsider_id = _make_user(db, "outsider3@example.com")
    post = post_service.create_post(author_id=author_id, content="Protected post")

    with pytest.raises(NotAuthorizedError):
        post_service.delete_post(post.id, author_id=outsider_id)


def test_post_service_has_no_reflex_dependency():
    with open(post_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source