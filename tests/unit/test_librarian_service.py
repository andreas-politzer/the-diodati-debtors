"""Tests for librarian_service: single-pass scoring, discretion
principle (visible vs. restricted matches), empty-visibility edge
case explicitly covered (per ChatGPT's review).
"""

from __future__ import annotations

import json

import pytest

from diodati_debtors.models.user import User
from diodati_debtors.services import book_service, group_service, librarian_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_book_with_embedding(db, owner_id: int, title: str, embedding: list[float]) -> int:
    book = book_service.create_book(owner_id=owner_id, title=title)
    with db() as session:
        from diodati_debtors.models.book import Book
        stored = session.get(Book, book.id)
        stored.embedding = json.dumps(embedding)
        session.commit()
    return book.id


def test_ask_librarian_finds_own_book(db, monkeypatch):
    owner_id = _make_user(db, "owner_lib1@example.com")
    _make_book_with_embedding(db, owner_id, "Frankenstein", [1.0, 0.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("a scientist creates life", owner_id)

    assert len(result.matches) == 1
    assert result.matches[0].title == "Frankenstein"
    assert result.restricted_hint is None
    assert result.no_match_at_all is False


def test_ask_librarian_no_match_when_nothing_crosses_threshold(db, monkeypatch):
    owner_id = _make_user(db, "owner_lib2@example.com")
    _make_book_with_embedding(db, owner_id, "Unrelated Book", [0.0, 1.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("completely different topic", owner_id)

    assert result.matches == []
    assert result.restricted_hint is None
    assert result.no_match_at_all is True


def test_ask_librarian_gives_restricted_hint_for_invisible_match(db, monkeypatch):
    outsider_id = _make_user(db, "outsider_lib1@example.com")
    owner_id = _make_user(db, "owner_lib3@example.com")
    group = group_service.create_group(founder_id=owner_id, name="Gothic Novel Society")
    _make_book_with_embedding(db, owner_id, "Secret Book", [1.0, 0.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("a scientist creates life", outsider_id)

    assert result.matches == []
    assert result.no_match_at_all is False
    assert result.restricted_hint is not None
    assert result.restricted_hint.club_name == "Gothic Novel Society"


def test_ask_librarian_reveals_match_to_fellow_club_member(db, monkeypatch):
    owner_id = _make_user(db, "owner_lib4@example.com")
    fellow_member_id = _make_user(db, "member_lib4@example.com")
    group = group_service.create_group(founder_id=owner_id, name="Late Romantics")
    group_service.approve_join_request(
        group_service.request_to_join(user_id=fellow_member_id, group_id=group.id).id,
        reviewer_id=owner_id,
    )
    _make_book_with_embedding(db, owner_id, "Shared Book", [1.0, 0.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("a scientist creates life", fellow_member_id)

    assert len(result.matches) == 1
    assert result.matches[0].title == "Shared Book"


def test_ask_librarian_handles_user_with_no_visible_books_at_all(db, monkeypatch):
    """Explicit empty-collection edge case, per ChatGPT's review:
    a user with zero books and zero clubs — visible_owner_ids is just
    {self}, and Book.owner_id.in_({self}) must not error out."""
    lonely_user_id = _make_user(db, "lonely_lib1@example.com")

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("anything at all", lonely_user_id)

    assert result.matches == []
    assert result.no_match_at_all is True


def test_librarian_service_has_no_reflex_dependency():
    with open(librarian_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source