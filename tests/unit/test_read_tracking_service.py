"""Tests for read_tracking_service — PostRead/CommentRead follow the
fachlich entity, not the UI projection (project vault, 02.08.)."""

from __future__ import annotations

from diodati_debtors.models.group import Group, GroupMembership
from diodati_debtors.models.post import Post
from diodati_debtors.models.comment import Comment
from diodati_debtors.models.user import User
from diodati_debtors.services import read_tracking_service
from diodati_debtors.models.group import Group


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_post(db, author_id: int, content: str) -> int:
    with db() as session:
        post = Post(author_id=author_id, content=content, post_type="general")
        session.add(post)
        session.commit()
        session.refresh(post)
        return post.id


def _make_comment(db, author_id: int, post_id: int, content: str) -> int:
    with db() as session:
        comment = Comment(author_id=author_id, post_id=post_id, content=content)
        session.add(comment)
        session.commit()
        session.refresh(comment)
        return comment.id


def test_mark_post_read_is_idempotent(db):
    user_id = _make_user(db, "read1@example.com")
    post_id = _make_post(db, user_id, "Hello")

    read_tracking_service.mark_post_read(post_id, user_id)
    read_tracking_service.mark_post_read(post_id, user_id)  # should not raise

    unread = read_tracking_service.get_unread_post_ids(user_id, [post_id])
    assert unread == set()


def test_get_unread_post_ids_returns_unread_only(db):
    user_id = _make_user(db, "read2@example.com")
    post_a = _make_post(db, user_id, "Post A")
    post_b = _make_post(db, user_id, "Post B")

    read_tracking_service.mark_post_read(post_a, user_id)

    unread = read_tracking_service.get_unread_post_ids(user_id, [post_a, post_b])

    assert unread == {post_b}


def test_get_unread_post_ids_empty_input_returns_empty_set():
    assert read_tracking_service.get_unread_post_ids(1, []) == set()


def test_marking_comment_read_does_not_affect_post_read_status(db):
    user_id = _make_user(db, "read3@example.com")
    post_id = _make_post(db, user_id, "Post with comment")
    comment_id = _make_comment(db, user_id, post_id, "A comment")

    read_tracking_service.mark_post_read(post_id, user_id)
    # New comment arrives after the post was read — post should stay read.
    unread_posts = read_tracking_service.get_unread_post_ids(user_id, [post_id])
    unread_comments = read_tracking_service.get_unread_comment_ids(user_id, [comment_id])

    assert unread_posts == set()
    assert unread_comments == {comment_id}


def test_get_unread_comment_ids_returns_unread_only(db):
    user_id = _make_user(db, "read4@example.com")
    post_id = _make_post(db, user_id, "Post")
    comment_a = _make_comment(db, user_id, post_id, "Comment A")
    comment_b = _make_comment(db, user_id, post_id, "Comment B")

    read_tracking_service.mark_comment_read(comment_a, user_id)

    unread = read_tracking_service.get_unread_comment_ids(user_id, [comment_a, comment_b])

    assert unread == {comment_b}

def test_count_unread_global_posts_counts_only_unread(db):
    author_id = _make_user(db, "count1@example.com")
    post_a = _make_post(db, author_id, "Global Post A")
    post_b = _make_post(db, author_id, "Global Post B")
    reader_id = _make_user(db, "count2@example.com")

    read_tracking_service.mark_post_read(post_a, reader_id)

    count = read_tracking_service.count_unread_global_posts(reader_id)

    assert count == 1


def test_count_unread_global_posts_excludes_club_and_book_posts(db):
    author_id = _make_user(db, "count3@example.com")
    reader_id = _make_user(db, "count4@example.com")
    _make_post(db, author_id, "Global Post")

    with db() as session:
        group = Group(name="Some Club", founder_id=author_id)
        session.add(group)
        session.commit()
        session.refresh(group)
        club_post = Post(author_id=author_id, content="Club Post", post_type="general", group_id=group.id)
        session.add(club_post)
        session.commit()

    count = read_tracking_service.count_unread_global_posts(reader_id)

    assert count == 1


def test_count_unread_club_posts_counts_only_that_clubs_unread(db):
    author_id = _make_user(db, "count5@example.com")
    reader_id = _make_user(db, "count6@example.com")

    with db() as session:
        group = Group(name="Test Club", founder_id=author_id)
        session.add(group)
        session.commit()
        session.refresh(group)
        group_id = group.id
        post_a = Post(author_id=author_id, content="Club Post A", post_type="general", group_id=group_id)
        post_b = Post(author_id=author_id, content="Club Post B", post_type="general", group_id=group_id)
        session.add_all([post_a, post_b])
        session.commit()
        session.refresh(post_a)

    read_tracking_service.mark_post_read(post_a.id, reader_id)

    count = read_tracking_service.count_unread_club_posts(reader_id, group_id)

    assert count == 1


def test_read_tracking_service_has_no_reflex_dependency():
    with open(read_tracking_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source