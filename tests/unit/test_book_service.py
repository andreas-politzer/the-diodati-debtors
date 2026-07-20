"""Tests for book_service.

Mirrors the pattern from test_loan_service.py: isolated in-memory
SQLite via the `db` fixture, deterministic inputs, no reliance on
dt.date.today() or wall-clock time.
"""

from __future__ import annotations

import datetime as dt

import pytest

from diodati_debtors.core.exceptions import (
    BookHasLoanHistoryError,
    BookHasPendingLoanRequestError,
    InvalidBookDataError,
    NotAuthorizedError,
    NotFoundError,
)
from diodati_debtors.models.group import Group, GroupMembership
from diodati_debtors.models.user import User
from diodati_debtors.services import book_service, loan_service
from diodati_debtors.core.exceptions import IsbnNotFoundError


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="Owner")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_group(db, name: str, founder_id: int) -> int:
    with db() as session:
        group = Group(name=name, founder_id=founder_id)
        session.add(group)
        session.commit()
        session.refresh(group)
        return group.id


def _add_membership(db, user_id: int, group_id: int) -> None:
    with db() as session:
        session.add(GroupMembership(user_id=user_id, group_id=group_id))
        session.commit()


def test_create_book_succeeds(db):
    owner_id = _make_user(db, "owner1@example.com")

    result = book_service.create_book(
        owner_id=owner_id,
        title="Frankenstein",
        author="Mary Shelley",
        isbn="9780141439471",
        location="Living room, green shelf",
    )

    assert result.owner_id == owner_id
    assert result.title == "Frankenstein"
    assert result.author == "Mary Shelley"
    assert result.isbn == "9780141439471"
    assert result.location == "Living room, green shelf"


def test_create_book_normalizes_whitespace_only_optional_fields_to_none(db):
    owner_id = _make_user(db, "owner2@example.com")

    result = book_service.create_book(
        owner_id=owner_id, title="Dracula", author="   ", isbn="  ", location="   "
    )

    assert result.author is None
    assert result.isbn is None
    assert result.location is None


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


def test_list_books_for_owner_returns_only_that_owners_books(db):
    owner_a = _make_user(db, "ownerA@example.com")
    owner_b = _make_user(db, "ownerB@example.com")
    book_a = book_service.create_book(owner_id=owner_a, title="Owner A's Book")
    book_service.create_book(owner_id=owner_b, title="Owner B's Book")

    books = book_service.list_books_for_owner(owner_a)

    assert [b.id for b in books] == [book_a.id]


def test_list_books_for_group_includes_all_members_books(db):
    founder_id = _make_user(db, "founder@example.com")
    member_id = _make_user(db, "member@example.com")
    outsider_id = _make_user(db, "outsider@example.com")
    group_id = _make_group(db, "Gothic Novel Society", founder_id=founder_id)
    _add_membership(db, founder_id, group_id)
    _add_membership(db, member_id, group_id)

    founder_book = book_service.create_book(owner_id=founder_id, title="Founder's Book")
    member_book = book_service.create_book(owner_id=member_id, title="Member's Book")
    book_service.create_book(owner_id=outsider_id, title="Outsider's Book")

    books = book_service.list_books_for_group(group_id)

    assert {b.id for b in books} == {founder_book.id, member_book.id}


def test_update_book_succeeds(db):
    owner_id = _make_user(db, "owner5@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Original Title")

    result = book_service.update_book(
        book.id, owner_id=owner_id, title="Updated Title", author="New Author"
    )

    assert result.title == "Updated Title"
    assert result.author == "New Author"


def test_update_book_rejects_non_owner(db):
    owner_id = _make_user(db, "owner6@example.com")
    outsider_id = _make_user(db, "outsider6@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Some Book")

    with pytest.raises(NotAuthorizedError):
        book_service.update_book(book.id, owner_id=outsider_id, title="Hijacked Title")


def test_update_book_rejects_blank_title(db):
    owner_id = _make_user(db, "owner7@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Some Book")

    with pytest.raises(InvalidBookDataError):
        book_service.update_book(book.id, owner_id=owner_id, title="   ")


def test_delete_book_succeeds_when_no_loan_history(db):
    owner_id = _make_user(db, "owner8@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Disposable Book")

    book_service.delete_book(book.id, owner_id=owner_id)

    with pytest.raises(NotFoundError):
        book_service.get_book(book.id)


def test_delete_book_rejects_non_owner(db):
    owner_id = _make_user(db, "owner9@example.com")
    outsider_id = _make_user(db, "outsider9@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Protected Book")

    with pytest.raises(NotAuthorizedError):
        book_service.delete_book(book.id, owner_id=outsider_id)


def test_delete_book_rejects_when_loan_history_exists(db):
    owner_id = _make_user(db, "owner10@example.com")
    borrower_id = _make_user(db, "borrower10@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Historic Book")
    returned = loan_service.create_loan(
        book_id=book.id, borrower_id=borrower_id, due_date=dt.date.today() + dt.timedelta(days=14)
    )
    loan_service.return_loan(returned.id, return_date=dt.date.today() + dt.timedelta(days=19))

    with pytest.raises(BookHasLoanHistoryError):
        book_service.delete_book(book.id, owner_id=owner_id)


def test_delete_book_rejects_when_pending_loan_request_exists(db):
    owner_id = _make_user(db, "owner11@example.com")
    requester_id = _make_user(db, "requester11@example.com")
    book = book_service.create_book(owner_id=owner_id, title="Requested Book")
    loan_service.request_to_borrow(book_id=book.id, requester_id=requester_id)

    with pytest.raises(BookHasPendingLoanRequestError):
        book_service.delete_book(book.id, owner_id=owner_id)

def test_lookup_isbn_returns_metadata_when_found(monkeypatch):
    def fake_fetch(isbn):
        return {
            "title": "Frankenstein",
            "authors": [{"name": "Mary Shelley"}],
            "publishers": [{"name": "Lackington, Hughes, Harding, Mavor & Jones"}],
            "publish_date": "1818",
            "cover": {"medium": "https://covers.example.com/frankenstein-m.jpg"},
        }

    monkeypatch.setattr(book_service, "fetch_book_by_isbn", fake_fetch)

    result = book_service.lookup_isbn("9780141439471")

    assert result.title == "Frankenstein"
    assert result.author == "Mary Shelley"
    assert result.publisher == "Lackington, Hughes, Harding, Mavor & Jones"
    assert result.publish_date == "1818"
    assert result.cover_url == "https://covers.example.com/frankenstein-m.jpg"


def test_lookup_isbn_raises_when_not_found(monkeypatch):
    monkeypatch.setattr(book_service, "fetch_book_by_isbn", lambda isbn: None)

    with pytest.raises(IsbnNotFoundError):
        book_service.lookup_isbn("0000000000")


def test_lookup_isbn_rejects_blank_isbn():
    with pytest.raises(IsbnNotFoundError):
        book_service.lookup_isbn("   ")


def test_lookup_isbn_handles_missing_optional_fields_gracefully(monkeypatch):
    def fake_fetch(isbn):
        return {"title": "Some Book"}  # no authors, publishers, cover, publish_date

    monkeypatch.setattr(book_service, "fetch_book_by_isbn", fake_fetch)

    result = book_service.lookup_isbn("1234567890")

    assert result.title == "Some Book"
    assert result.author is None
    assert result.publisher is None
    assert result.publish_date is None
    assert result.cover_url is None


def test_book_service_has_no_reflex_dependency():
    """Static source check, per the Architecture Contract."""
    with open(book_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source