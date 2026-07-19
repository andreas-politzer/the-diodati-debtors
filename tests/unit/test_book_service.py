"""Tests for book_service.

Mirrors the pattern from test_loan_service.py: isolated in-memory
SQLite via the `db` fixture, deterministic inputs, no reliance on
dt.date.today() or wall-clock time.
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import InvalidBookDataError, NotFoundError
from diodati_debtors.models.user import User
from diodati_debtors.services import book_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="Owner")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_create_book_succeeds(db):
    owner_id = _make_user(db, "owner1@example.com")

    result = book_service.create_book(
        owner_id=owner_id, title="Frankenstein", author="Mary Shelley", isbn="9780141439471"
    )

    assert result.owner_id == owner_id
    assert result.title == "Frankenstein"
    assert result.author == "Mary Shelley"
    assert result.isbn == "9780141439471"


def test_create_book_normalizes_whitespace_only_optional_fields_to_none(db):
    owner_id = _make_user(db, "owner2@example.com")

    result = book_service.create_book(
        owner_id=owner_id, title="Dracula", author="   ", isbn="  "
    )

    assert result.author is None
    assert result.isbn is None


def test_create_book_rejects_blank_title(db):
    owner_id = _make_user(db, "owner3@example.com")

    with pytest.raises(InvalidBookDataError):
        book_service.create_book(owner_id=owner_id, title="   ")


def test_create_book_rejects_unknown_owner(db):
    with pytest.raises(NotFoundError):
        book_service.create_book(owner_id=999, title="The Vampyre")


def test_get_book_raises_when_missing(db):
    with pytest.raises(NotFoundError):
        book_service.get_book(999)


def test_list_books_returns_all_in_creation_order(db):
    owner_id = _make_user(db, "owner4@example.com")
    first = book_service.create_book(owner_id=owner_id, title="First")
    second = book_service.create_book(owner_id=owner_id, title="Second")

    books = book_service.list_books()

    assert [b.id for b in books] == [first.id, second.id]


def test_book_service_has_no_reflex_dependency():
    """Static source check, per the Architecture Contract."""
    with open(book_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source