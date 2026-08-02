"""Personal Messages state — the contact-oriented list of all Club
Conversations for the current user (per the 02.08. UX decision,
project vault): one entry per person, not per message, like WhatsApp.
A search field filters by name — scrolling happens within the list
itself, not the whole page.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import club_conversation_service, user_service
from .auth_state import AuthState
from ..core.formatting import format_datetime_human


@dataclass
class PersonalMessageEntry:
    conversation_id: int
    other_person_name: str
    last_message_preview: str
    last_message_at: str
    unread_count: int


class PersonalMessagesState(rx.State):
    entries: list[PersonalMessageEntry] = []
    search_query: str = ""
    error_message: str = ""

    def set_search_query(self, value: str):
        self.search_query = value

    @rx.var
    def filtered_entries(self) -> list[PersonalMessageEntry]:
        if not self.search_query.strip():
            return self.entries
        query_lower = self.search_query.strip().lower()
        return [e for e in self.entries if query_lower in e.other_person_name.lower()]

    async def load_entries(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.entries = []
            return

        current_user_id = int(auth_state.current_user_id)

        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        names_by_id = {u.id: u.display_name for u in user_results}

        try:
            conversations = club_conversation_service.list_conversations_for_user(current_user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        entries: list[PersonalMessageEntry] = []
        for conversation in conversations:
            if not conversation.messages:
                continue
            other_id = (
                conversation.recipient_id
                if conversation.initiator_id == current_user_id
                else conversation.initiator_id
            )
            last_message = conversation.messages[-1]
            unread = sum(
                1 for m in conversation.messages
                if m.sender_id != current_user_id and m.read_at is None
            )
            entries.append(
                PersonalMessageEntry(
                    conversation_id=conversation.id,
                    other_person_name=names_by_id.get(other_id, f"User {other_id}"),
                    last_message_preview=last_message.content[:80],
                    last_message_at=format_datetime_human(last_message.sent_at),
                    unread_count=unread,
                )
            )

        entries.sort(key=lambda e: e.last_message_at, reverse=True)
        self.entries = entries


__all__ = ["PersonalMessagesState", "PersonalMessageEntry"]