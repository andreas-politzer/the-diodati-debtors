"""Club Conversation Detail state — the complete message history of
one specific ClubConversation, plus the ability to reply. Reading
(marking messages as read) happens automatically on load, per the
domain session decision.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError, NotAuthorizedError, NotFoundError
from ..services import club_conversation_service, user_service
from .auth_state import AuthState
from ..ui.components.avatar import compute_initials


@dataclass
class ClubMessageView:
    id: int
    sender_display_name: str
    sender_monogram: str
    content: str
    sent_at: str
    is_own: bool


class ClubConversationDetailState(rx.State):
    loaded_conversation_id: int = 0
    other_person_id: int = 0
    other_person_name: str = ""
    messages: list[ClubMessageView] = []
    reply_draft: str = ""
    error_message: str = ""

    def set_reply_draft(self, value: str):
        self.reply_draft = value

    async def load_conversation(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return

        try:
            conv_id = int(self.conversation_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid conversation id."
            return

        current_user_id = int(auth_state.current_user_id)

        try:
            result = club_conversation_service.open_conversation(conv_id, viewer_id=current_user_id)
        except NotFoundError:
            self.error_message = "This conversation does not exist."
            return
        except NotAuthorizedError:
            self.error_message = "You do not have permission to view this conversation."
            return
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.loaded_conversation_id = result.id
        self.other_person_id = (
            result.recipient_id if result.initiator_id == current_user_id else result.initiator_id
        )
        try:
            other_user = user_service.get_user(self.other_person_id)
            self.other_person_name = other_user.display_name
        except DiodatiError:
            self.other_person_name = f"User {self.other_person_id}"

        self.messages = [
            ClubMessageView(
                id=m.id,
                sender_display_name=self.other_person_name if m.sender_id == self.other_person_id else "You",
                sender_monogram=compute_initials(
                    self.other_person_name if m.sender_id == self.other_person_id else "You"
                ),
                content=m.content,
                sent_at=m.sent_at.isoformat(),
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
            club_conversation_service.send_message(
                current_user_id, self.other_person_id, self.reply_draft
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.reply_draft = ""
        await self.load_conversation()


__all__ = ["ClubConversationDetailState", "ClubMessageView"]