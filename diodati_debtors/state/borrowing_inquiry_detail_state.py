"""Borrowing Inquiry Detail state — the complete message history of
one specific BorrowingInquiry, plus the ability to reply or close it.
Reading (marking messages as read) happens automatically on load, per
the domain session decision (same principle as Club Conversation).
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError, NotAuthorizedError, NotFoundError
from ..core.formatting import format_datetime_human
from ..services import book_service, borrowing_inquiry_service, user_service
from ..ui.components.avatar import compute_initials
from .auth_state import AuthState


@dataclass
class InquiryMessageView:
    id: int
    sender_display_name: str
    sender_monogram: str
    content: str
    sent_at: str
    is_own: bool


class BorrowingInquiryDetailState(rx.State):
    loaded_inquiry_id: int = 0
    loaded_book_id: int = 0
    book_title: str = ""
    other_person_id: int = 0
    other_person_name: str = ""
    status: str = ""
    messages: list[InquiryMessageView] = []
    reply_draft: str = ""
    error_message: str = ""
    info_message: str = ""

    def set_reply_draft(self, value: str):
        self.reply_draft = value

    async def load_inquiry(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return

        try:
            inq_id = int(self.inquiry_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid inquiry id."
            return

        current_user_id = int(auth_state.current_user_id)

        try:
            result = borrowing_inquiry_service.open_inquiry(inq_id, viewer_id=current_user_id)
        except NotFoundError:
            self.error_message = "This inquiry does not exist."
            return
        except NotAuthorizedError:
            self.error_message = "You do not have permission to view this inquiry."
            return
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.loaded_inquiry_id = result.id
        self.loaded_book_id = result.book_id
        self.status = result.status
        self.other_person_id = (
            result.owner_id if result.requester_id == current_user_id else result.requester_id
        )

        try:
            self.book_title = book_service.get_book(current_user_id, result.book_id).title
        except DiodatiError:
            self.book_title = f"Book {result.book_id}"

        try:
            other_user = user_service.get_user(self.other_person_id)
            self.other_person_name = other_user.display_name
        except DiodatiError:
            self.other_person_name = f"User {self.other_person_id}"

        self.messages = [
            InquiryMessageView(
                id=m.id,
                sender_display_name=self.other_person_name if m.sender_id == self.other_person_id else "You",
                sender_monogram=compute_initials(
                    self.other_person_name if m.sender_id == self.other_person_id else "You"
                ),
                content=m.content,
                sent_at=format_datetime_human(m.sent_at),
                is_own=(m.sender_id == current_user_id),
            )
            for m in result.messages
        ]

    async def send_reply(self):
        self.error_message = ""
        if not self.reply_draft.strip():
            self.error_message = "Write a message first."
            return

        auth_state = await self.get_state(AuthState)
        current_user_id = int(auth_state.current_user_id)

        try:
            borrowing_inquiry_service.reply(self.loaded_inquiry_id, current_user_id, self.reply_draft)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.reply_draft = ""
        await self.load_inquiry()

    async def close(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        current_user_id = int(auth_state.current_user_id)

        try:
            borrowing_inquiry_service.close_inquiry(self.loaded_inquiry_id, current_user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.info_message = "Inquiry closed."
        await self.load_inquiry()


__all__ = ["BorrowingInquiryDetailState", "InquiryMessageView"]