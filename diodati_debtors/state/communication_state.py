"""Communication state — the unified overview of ongoing bibliothekarisch
processes that involve messages (Borrowing Inquiries, Club
Conversations). Per ChatGPT's review (01.08., project vault): this is
an inbox/work-list, not a messenger. Each row represents a PROCESS,
not a "conversation" — the underlying fachlich separation (two
distinct services, two distinct tables) is preserved; only the
overview list merges them for display purposes.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import (
    book_service,
    borrowing_inquiry_service,
    club_conversation_service,
    user_service,
)
from .auth_state import AuthState


@dataclass
class CommunicationRow:
    process_type: str  # "borrowing_inquiry" | "club_conversation"
    process_id: int
    other_person_name: str
    label: str  # "Borrowing Inquiry" | "Club Conversation"
    subject: str  # book title, or "Direct message"
    last_message_preview: str
    last_message_at: str
    last_message_is_own: bool


class CommunicationState(rx.State):
    rows: list[CommunicationRow] = []
    error_message: str = ""

    async def load_rows(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.rows = []
            return

        current_user_id = int(auth_state.current_user_id)

        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        names_by_id = {u.id: u.display_name for u in user_results}

        rows: list[CommunicationRow] = []

        try:
            inquiries = borrowing_inquiry_service.list_inquiries_for_user(current_user_id)
        except DiodatiError:
            inquiries = []

        for inquiry in inquiries:
            if not inquiry.messages:
                continue
            other_id = (
                inquiry.owner_id if inquiry.requester_id == current_user_id else inquiry.requester_id
            )
            try:
                book_title = book_service.get_book(inquiry.book_id).title
            except DiodatiError:
                book_title = f"Book {inquiry.book_id}"
            last_message = inquiry.messages[-1]
            rows.append(
                CommunicationRow(
                    process_type="borrowing_inquiry",
                    process_id=inquiry.id,
                    other_person_name=names_by_id.get(other_id, f"User {other_id}"),
                    label="Borrowing Inquiry",
                    subject=book_title,
                    last_message_preview=last_message.content[:80],
                    last_message_at=last_message.sent_at.isoformat(),
                    last_message_is_own=(last_message.sender_id == current_user_id),
                )
            )

        try:
            conversations = club_conversation_service.list_conversations_for_user(current_user_id)
        except DiodatiError:
            conversations = []

        for conversation in conversations:
            if not conversation.messages:
                continue
            other_id = (
                conversation.recipient_id
                if conversation.initiator_id == current_user_id
                else conversation.initiator_id
            )
            last_message = conversation.messages[-1]
            rows.append(
                CommunicationRow(
                    process_type="club_conversation",
                    process_id=conversation.id,
                    other_person_name=names_by_id.get(other_id, f"User {other_id}"),
                    label="Club Conversation",
                    subject="Direct message",
                    last_message_preview=last_message.content[:80],
                    last_message_at=last_message.sent_at.isoformat(),
                    last_message_is_own=(last_message.sender_id == current_user_id),
                )
            )

        rows.sort(key=lambda r: r.last_message_at, reverse=True)
        self.rows = rows

    unread_count: int = 0

    async def load_unread_count(self):
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.unread_count = 0
            return

        current_user_id = int(auth_state.current_user_id)
        count = 0

        try:
            inquiries = borrowing_inquiry_service.list_inquiries_for_user(current_user_id)
            for inquiry in inquiries:
                count += sum(
                    1 for m in inquiry.messages
                    if m.sender_id != current_user_id and m.read_at is None
                )
        except DiodatiError:
            pass

        try:
            conversations = club_conversation_service.list_conversations_for_user(current_user_id)
            for conversation in conversations:
                count += sum(
                    1 for m in conversation.messages
                    if m.sender_id != current_user_id and m.read_at is None
                )
        except DiodatiError:
            pass

        self.unread_count = count


__all__ = ["CommunicationState", "CommunicationRow"]