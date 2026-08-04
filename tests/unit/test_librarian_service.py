"""Tests for librarian_service: single-pass scoring, discretion
principle (visible vs. restricted matches), the direct-title fast
path, multi-book external recommendations with a shared Byron-voiced
remark, and the explicit empty-visibility edge case.
"""

from __future__ import annotations

import json

import pytest

from diodati_debtors.models.user import User
from diodati_debtors.services import book_service, group_service, librarian_service


def _make_user(db, email: str, *, verified: bool = True) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User", email_verified=verified)
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
    _make_book_with_embedding(db, owner_id, "Some Unrelated Title Entirely", [1.0, 0.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("a scientist creates life", owner_id)

    assert len(result.matches) == 1
    assert result.matches[0].title == "Some Unrelated Title Entirely"
    assert result.restricted_hint is None


def test_ask_librarian_direct_title_match_bypasses_embedding_threshold(db, monkeypatch):
    """The fast path: an exact title mentioned in the query is always
    a match, regardless of embedding similarity — catches "do you have
    X?" questions pure semantic scoring can under-rank."""
    owner_id = _make_user(db, "owner_lib_title@example.com")
    _make_book_with_embedding(db, owner_id, "At the Mountains of Madness", [0.0, 1.0, 0.0])

    # Deliberately mismatched embedding — the direct title check must
    # still find it without ever calling embed_text for scoring.
    monkeypatch.setattr(
        librarian_service, "embed_text",
        lambda q, task_type="RETRIEVAL_QUERY": (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    result = librarian_service.ask_librarian("do you have At the Mountains of Madness?", owner_id)

    assert len(result.matches) == 1
    assert result.matches[0].title == "At the Mountains of Madness"


def test_ask_librarian_no_match_when_nothing_crosses_threshold(db, monkeypatch):
    owner_id = _make_user(db, "owner_lib2@example.com")
    _make_book_with_embedding(db, owner_id, "Unrelated Book", [0.0, 1.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("completely different topic", owner_id)

    assert result.matches == []
    assert result.restricted_hint is None


def test_ask_librarian_gives_restricted_hint_for_invisible_match(db, monkeypatch):
    outsider_id = _make_user(db, "outsider_lib1@example.com")
    owner_id = _make_user(db, "owner_lib3@example.com")
    group_service.create_group(founder_id=owner_id, name="Gothic Novel Society")
    _make_book_with_embedding(db, owner_id, "Secret Book", [1.0, 0.0, 0.0])

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("a scientist creates life", outsider_id)

    assert result.matches == []
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
    """Explicit empty-collection edge case, per ChatGPT's review: a
    user with zero books and zero clubs — visible_owner_ids is just
    {self}, and the underlying queries must not error out."""
    lonely_user_id = _make_user(db, "lonely_lib1@example.com")

    monkeypatch.setattr(librarian_service, "embed_text", lambda q, task_type="RETRIEVAL_QUERY": [1.0, 0.0, 0.0])

    result = librarian_service.ask_librarian("anything at all", lonely_user_id)

    assert result.matches == []
    assert result.restricted_hint is None


def test_get_external_recommendation_success(monkeypatch):
    query = "a very serious scientist attempts to create life artificially"

    def fake_generate_text(prompt):
        if "candidate_books" in prompt:
            return '{"answer": "", "candidate_books": [{"title": "Frankenstein", "author": "Mary Shelley"}]}'
        return "Ah, Frankenstein indeed!"

    monkeypatch.setattr(librarian_service, "generate_text", fake_generate_text)

    from diodati_debtors.services.external.google_books_client import GoogleBookResult

    fake_result = GoogleBookResult(
        title="Frankenstein", author="Mary Shelley",
        isbn="9780141439471", cover_url="http://example.com/cover.jpg", info_link=None,
    )
    monkeypatch.setattr(
        librarian_service.google_books_client, "search_books",
        lambda q, max_results=5: [fake_result],
    )

    result = librarian_service.get_external_recommendation(query)

    assert result is not None
    assert result.books[0].title == "Frankenstein"
    assert result.books[0].author == "Mary Shelley"


def test_get_external_recommendation_falls_back_without_open_library_match(monkeypatch):
    """Renamed intent (per the 28.07 hard-verification fix): an
    unverifiable candidate is silently dropped, never shown as a
    "fact" — but a factual answer alone (without any book) is still a
    valid, non-None result."""
    query = "please recommend me a genuinely quite obscure forgotten book"

    def fake_generate_text(prompt):
        if "candidate_books" in prompt:
            return (
                '{"answer": "I could not verify a specific title, but this '
                'theme is common in gothic literature.", '
                '"candidate_books": [{"title": "Some Rare Book", "author": "Some Author"}]}'
            )
        return "Alas, I cannot confirm a specific volume, but take heart..."

    monkeypatch.setattr(librarian_service, "generate_text", fake_generate_text)
    monkeypatch.setattr(
        librarian_service.google_books_client, "search_books",
        lambda q, max_results=5: [],
    )

    result = librarian_service.get_external_recommendation(query)

    assert result is not None
    assert result.books == []
    assert result.remark


def test_get_external_recommendation_parses_multiple_books(monkeypatch):
    query = "please give me three completely different classic novel suggestions"

    def fake_generate_text(prompt):
        if "candidate_books" in prompt:
            return (
                '{"answer": "", "candidate_books": ['
                '{"title": "Book One", "author": "Author One"}, '
                '{"title": "Book Two", "author": "Author Two"}, '
                '{"title": "Book Three", "author": "Author Three"}]}'
            )
        return "Here are three splendid choices!"

    monkeypatch.setattr(librarian_service, "generate_text", fake_generate_text)

    from diodati_debtors.services.external.google_books_client import GoogleBookResult

    def fake_search(query, max_results=5):
        if "Book One" in query:
            return [GoogleBookResult(title="Book One", author="Author One", isbn=None, cover_url=None, info_link=None)]
        if "Book Two" in query:
            return [GoogleBookResult(title="Book Two", author="Author Two", isbn=None, cover_url=None, info_link=None)]
        if "Book Three" in query:
            return [GoogleBookResult(title="Book Three", author="Author Three", isbn=None, cover_url=None, info_link=None)]
        return []

    monkeypatch.setattr(librarian_service.google_books_client, "search_books", fake_search)

    result = librarian_service.get_external_recommendation(query)

    assert result is not None
    assert len(result.books) == 3
    assert [b.title for b in result.books] == ["Book One", "Book Two", "Book Three"]


def test_get_external_recommendation_returns_none_on_unparseable_response(monkeypatch):
    monkeypatch.setattr(librarian_service, "generate_text", lambda prompt: "I don't know what to suggest.")

    result = librarian_service.get_external_recommendation("something weird")

    assert result is None


def test_get_external_recommendation_returns_none_on_gemini_failure(monkeypatch):
    def failing_generate(prompt):
        raise ValueError("simulated outage")

    monkeypatch.setattr(librarian_service, "generate_text", failing_generate)

    result = librarian_service.get_external_recommendation("anything")

    assert result is None


def test_get_match_remark_returns_text(monkeypatch):
    monkeypatch.setattr(librarian_service, "generate_text", lambda prompt: "Ah, a fine choice indeed!")

    from diodati_debtors.services.librarian_service import LibrarianMatch

    matches = [LibrarianMatch(book_id=1, title="Frankenstein", author="Mary Shelley", similarity=0.9)]
    remark = librarian_service.get_match_remark("a scientist creates life", matches)

    assert remark == "Ah, a fine choice indeed!"


def test_get_match_remark_falls_back_on_gemini_failure(monkeypatch):
    def failing_generate(prompt):
        raise ValueError("simulated outage")

    monkeypatch.setattr(librarian_service, "generate_text", failing_generate)

    from diodati_debtors.services.librarian_service import LibrarianMatch

    matches = [LibrarianMatch(book_id=1, title="Frankenstein", author="Mary Shelley", similarity=0.9)]
    remark = librarian_service.get_match_remark("a scientist creates life", matches)

    assert "Frankenstein" in remark


def test_librarian_service_has_no_reflex_dependency():
    with open(librarian_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source