"""Communication state — the Hub overview: three cards (Personal
Messages, Club Feed, Global Board), each with an unread count and a
preview of the latest activity. Per the 02.08. architecture decision
(project vault): Communication is a pure entry point, not a content
page. Borrowing Inquiry deliberately does NOT appear here — it's
vorgangs-/book-bound, not personen-bound, and lives in Organize
instead (see Personal Messages Domain Model, project vault).

Architecture note: unread counts are plain, top-level State fields
(loaded directly by services), NOT embedded in the Preview dataclasses
— Service loads data, State stores it, @rx.var derives only the
aggregate total. This avoids coupling the display-oriented Preview
shape to the fachlich unread-count concept.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import club_conversation_service, post_service, read_tracking_service, user_service
from .auth_state import AuthState
from .group_state import GroupState
from ..core.formatting import format_datetime_human


@dataclass
class PersonalMessagesPreview:
    has_any: bool = False
    other_person_name: str = ""
    last_message_preview: str = ""
    last_message_at: str = ""


@dataclass
class FeedPreview:
    has_any: bool = False
    author_name: str = ""
    content_preview: str = ""
    posted_at: str = ""

@dataclass
class ClubConversationListEntry:
    conversation_id: int
    other_person_name: str
    last_message_preview: str
    last_message_at: str
    unread_count: int


class CommunicationState(rx.State):
    personal_messages: PersonalMessagesPreview = PersonalMessagesPreview()
    club_feed: FeedPreview = FeedPreview()
    global_board: FeedPreview = FeedPreview()

    unread_personal_messages: int = 0
    unread_club_feed: int = 0
    unread_global_board: int = 0

    error_message: str = ""

    async def load_hub(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            return

        current_user_id = int(auth_state.current_user_id)

        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        names_by_id = {u.id: u.display_name for u in user_results}

        # --- Personal Messages (Club Conversations only) ---
        try:
            conversations = club_conversation_service.list_conversations_for_user(current_user_id)
        except DiodatiError:
            conversations = []

        conversations_with_messages = [c for c in conversations if c.messages]
        self.unread_personal_messages = sum(
            sum(1 for m in c.messages if m.sender_id != current_user_id and m.read_at is None)
            for c in conversations_with_messages
        )

        if conversations_with_messages:
            latest = max(conversations_with_messages, key=lambda c: c.messages[-1].sent_at)
            other_id = (
                latest.recipient_id if latest.initiator_id == current_user_id else latest.initiator_id
            )
            last_message = latest.messages[-1]
            self.personal_messages = PersonalMessagesPreview(
                has_any=True,
                other_person_name=names_by_id.get(other_id, f"User {other_id}"),
                last_message_preview=last_message.content[:80],
                last_message_at=format_datetime_human(last_message.sent_at),
            )
        else:
            self.personal_messages = PersonalMessagesPreview()

        # --- Club Feed (only if a club is selected) ---
        group_state = await self.get_state(GroupState)
        if group_state.current_group_id:
            group_id = int(group_state.current_group_id)
            try:
                club_posts = post_service.list_club_feed_posts(group_id)
            except DiodatiError:
                club_posts = []

            self.unread_club_feed = read_tracking_service.count_unread_club_posts(
                current_user_id, group_id
            )
            if club_posts:
                latest_post = max(club_posts, key=lambda p: p.created_at)
                self.club_feed = FeedPreview(
                    has_any=True,
                    author_name=names_by_id.get(latest_post.author_id, f"User {latest_post.author_id}"),
                    content_preview=latest_post.content[:80],
                    posted_at=format_datetime_human(latest_post.created_at),
                )
            else:
                self.club_feed = FeedPreview()
        else:
            self.unread_club_feed = 0
            self.club_feed = FeedPreview()

        # --- Global Board ---
        try:
            board_posts = post_service.list_global_board_posts()
        except DiodatiError:
            board_posts = []

        self.unread_global_board = read_tracking_service.count_unread_global_posts(current_user_id)
        if board_posts:
            latest_post = max(board_posts, key=lambda p: p.created_at)
            self.global_board = FeedPreview(
                has_any=True,
                author_name=names_by_id.get(latest_post.author_id, f"User {latest_post.author_id}"),
                content_preview=latest_post.content[:80],
                posted_at=format_datetime_human(latest_post.created_at),
            )
        else:
            self.global_board = FeedPreview()

    @rx.var
    def total_unread_count(self) -> int:
        return self.unread_personal_messages + self.unread_club_feed + self.unread_global_board


__all__ = ["CommunicationState", "PersonalMessagesPreview", "FeedPreview"]