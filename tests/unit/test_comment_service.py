"""Tests for comment_service: one comment system for every Post,
author-only deletion.
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import (
    InvalidPostDataError,
    NotAuthorizedError,
    NotFoundError,
)
from diodati_debtors.models.user import User
from diodati_debtors.services import comment_service, post_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_create_comment_succeeds(db):
    author_id = _make_user(db, "author1@example.com")
    commenter_id = _make_user(db, "commenter1@example.com")
    post = post_service.create_post(author_id=author_id, content="A post")

    result = comment_service.create_comment(
        post_id=post.id, author_id=commenter_id, content="Nice post!"
    )

    assert result.post_id == post.id
    assert result.author_id == commenter_id


def test_create_comment_rejects_blank_content(db):
    author_id = _make_user(db, "author2@example.com")
    post = post_service.create_post(author_id=author_id, content="A post")

    with pytest.raises(InvalidPostDataError):
        comment_service.create_comment(post_id=post.id, author_id=author_id, content="   ")


def test_create_comment_rejects_unknown_post(db):
    author_id = _make_user(db, "author3@example.com")

    with pytest.raises(NotFoundError):
        comment_service.create_comment(post_id=999, author_id=author_id, content="Hello")


def test_list_comments_for_post_returns_oldest_first(db):
    author_id = _make_user(db, "author4@example.com")
    post = post_service.create_post(author_id=author_id, content="A post")

    first = comment_service.create_comment(post_id=post.id, author_id=author_id, content="First")
    second = comment_service.create_comment(post_id=post.id, author_id=author_id, content="Second")

    results = comment_service.list_comments_for_post(post.id)

    assert [r.id for r in results] == [first.id, second.id]


def test_delete_comment_succeeds_for_author(db):
    author_id = _make_user(db, "author5@example.com")
    post = post_service.create_post(author_id=author_id, content="A post")
    comment = comment_service.create_comment(post_id=post.id, author_id=author_id, content="Mine")

    comment_service.delete_comment(comment.id, author_id=author_id)

    results = comment_service.list_comments_for_post(post.id)
    assert results == []


def test_delete_comment_rejects_non_author(db):
    author_id = _make_user(db, "author6@example.com")
    outsider_id = _make_user(db, "outsider1@example.com")
    post = post_service.create_post(author_id=author_id, content="A post")
    comment = comment_service.create_comment(
        post_id=post.id, author_id=author_id, content="Protected"
    )

    with pytest.raises(NotAuthorizedError):
        comment_service.delete_comment(comment.id, author_id=outsider_id)


def test_comment_service_has_no_reflex_dependency():
    with open(comment_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source