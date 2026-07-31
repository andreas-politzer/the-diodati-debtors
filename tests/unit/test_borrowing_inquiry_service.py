"""Tests for borrowing_inquiry_service — the Public Borrowing Inquiry
process (project vault: Personal Messages Domain Model)."""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import NotAuthorizedError, NotFoundError
from diodati_debtors.models.book import Book
from diodati_debtors.models.enums import BorrowingVisibility, ProfileVisibility
from diodati_debtors.models.user import User
from diodati_debtors.services import borrowing_inquiry_service, profile_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_book(db, owner_id: int, title: str, borrowing_visibility=BorrowingVisibility.PUBLIC_ENQUIRIES_ALLOWED) -> int:
    with db() as session:
        book = Book(owner_id=owner_id, title=title, borrowing_visibility=borrowing_visibility)
        session.add(book)
        session.commit()
        session.refresh(book)
        return book.id


def test_start_inquiry_creates_inquiry_with_first_message(db):
    owner_id = _make_user(db, "owner_inq1@example.com")
    requester_id = _make_user(db, "requester_inq1@example.com")
    book_id = _make_book(db, owner_id, "Frankenstein")

    result = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi, is this still available?")

    assert result.status == "open"
    assert len(result.messages) == 1
    assert result.messages[0].content == "Hi, is this still available?"
    assert result.messages[0].sender_id == requester_id


def test_start_inquiry_rejects_club_only_book(db):
    owner_id = _make_user(db, "owner_inq2@example.com")
    requester_id = _make_user(db, "requester_inq2@example.com")
    book_id = _make_book(db, owner_id, "Dracula", borrowing_visibility=BorrowingVisibility.CLUB_ONLY)

    with pytest.raises(borrowing_inquiry_service.InquiryNotAllowedError):
        borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")


def test_start_inquiry_rejects_when_owner_profile_is_private(db):
    owner_id = _make_user(db, "owner_inq3@example.com")
    requester_id = _make_user(db, "requester_inq3@example.com")
    book_id = _make_book(db, owner_id, "The Vampyre")
    profile_service.update_profile(owner_id, visibility="private")

    with pytest.raises(borrowing_inquiry_service.InquiryNotAllowedError):
        borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")


def test_start_inquiry_rejects_duplicate_open_inquiry(db):
    owner_id = _make_user(db, "owner_inq4@example.com")
    requester_id = _make_user(db, "requester_inq4@example.com")
    book_id = _make_book(db, owner_id, "Carmilla")
    borrowing_inquiry_service.start_inquiry(book_id, requester_id, "First try")

    with pytest.raises(borrowing_inquiry_service.DuplicateOpenInquiryError):
        borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Second try")


def test_start_inquiry_allows_new_one_after_previous_closed(db):
    owner_id = _make_user(db, "owner_inq5@example.com")
    requester_id = _make_user(db, "requester_inq5@example.com")
    book_id = _make_book(db, owner_id, "The King in Yellow")
    first = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "First try")
    borrowing_inquiry_service.close_inquiry(first.id, closer_id=requester_id)

    second = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Second try")

    assert second.id != first.id
    assert second.status == "open"


def test_reply_adds_message_from_either_participant(db):
    owner_id = _make_user(db, "owner_inq6@example.com")
    requester_id = _make_user(db, "requester_inq6@example.com")
    book_id = _make_book(db, owner_id, "The Turn of the Screw")
    inquiry = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")

    result = borrowing_inquiry_service.reply(inquiry.id, sender_id=owner_id, message="Sure, come by!")

    assert len(result.messages) == 2
    assert result.messages[1].sender_id == owner_id


def test_reply_rejects_non_participant(db):
    owner_id = _make_user(db, "owner_inq7@example.com")
    requester_id = _make_user(db, "requester_inq7@example.com")
    outsider_id = _make_user(db, "outsider_inq1@example.com")
    book_id = _make_book(db, owner_id, "We Have Always Lived in the Castle")
    inquiry = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")

    with pytest.raises(NotAuthorizedError):
        borrowing_inquiry_service.reply(inquiry.id, sender_id=outsider_id, message="Butting in")


def test_reply_rejects_message_on_closed_inquiry(db):
    owner_id = _make_user(db, "owner_inq8@example.com")
    requester_id = _make_user(db, "requester_inq8@example.com")
    book_id = _make_book(db, owner_id, "The Yellow Wallpaper")
    inquiry = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")
    borrowing_inquiry_service.close_inquiry(inquiry.id, closer_id=requester_id)

    with pytest.raises(borrowing_inquiry_service.InquiryNotAllowedError):
        borrowing_inquiry_service.reply(inquiry.id, sender_id=owner_id, message="Too late")


def test_close_inquiry_rejects_non_participant(db):
    owner_id = _make_user(db, "owner_inq9@example.com")
    requester_id = _make_user(db, "requester_inq9@example.com")
    outsider_id = _make_user(db, "outsider_inq2@example.com")
    book_id = _make_book(db, owner_id, "Frankenstein in Baghdad")
    inquiry = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")

    with pytest.raises(NotAuthorizedError):
        borrowing_inquiry_service.close_inquiry(inquiry.id, closer_id=outsider_id)


def test_list_inquiries_for_user_includes_both_roles(db):
    owner_id = _make_user(db, "owner_inq10@example.com")
    requester_id = _make_user(db, "requester_inq10@example.com")
    book_a = _make_book(db, owner_id, "Book A")
    book_b = _make_book(db, requester_id, "Book B")
    borrowing_inquiry_service.start_inquiry(book_a, requester_id, "As requester")
    borrowing_inquiry_service.start_inquiry(book_b, owner_id, "As owner of book B, requesting book A's owner's book")

    results = borrowing_inquiry_service.list_inquiries_for_user(requester_id)

    assert len(results) == 2


def test_open_inquiry_marks_messages_addressed_to_viewer_as_read(db):
    owner_id = _make_user(db, "owner_inq11@example.com")
    requester_id = _make_user(db, "requester_inq11@example.com")
    book_id = _make_book(db, owner_id, "At the Mountains of Madness")
    inquiry = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")
    borrowing_inquiry_service.reply(inquiry.id, sender_id=owner_id, message="Sure!")

    result = borrowing_inquiry_service.open_inquiry(inquiry.id, viewer_id=requester_id)

    owner_message = next(m for m in result.messages if m.sender_id == owner_id)
    assert owner_message.read_at is not None

    requester_message = next(m for m in result.messages if m.sender_id == requester_id)
    assert requester_message.read_at is None


def test_open_inquiry_rejects_non_participant(db):
    owner_id = _make_user(db, "owner_inq12@example.com")
    requester_id = _make_user(db, "requester_inq12@example.com")
    outsider_id = _make_user(db, "outsider_inq3@example.com")
    book_id = _make_book(db, owner_id, "The Colour Out of Space")
    inquiry = borrowing_inquiry_service.start_inquiry(book_id, requester_id, "Hi!")

    with pytest.raises(NotAuthorizedError):
        borrowing_inquiry_service.open_inquiry(inquiry.id, viewer_id=outsider_id)


def test_borrowing_inquiry_service_has_no_reflex_dependency():
    with open(borrowing_inquiry_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source