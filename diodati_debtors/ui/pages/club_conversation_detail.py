"""Club Conversation Detail — complete message history between two
same-club members, with a reply form. No chat-bubble styling — kept
consistent with the project's flat, restrained visual language.
"""

from __future__ import annotations

import reflex as rx

from ..components.avatar import avatar
from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.club_conversation_detail_state import ClubConversationDetailState, ClubMessageView


def _message_row(message: ClubMessageView) -> rx.Component:
    return rx.hstack(
        avatar(message.sender_monogram, size="24px"),
        rx.vstack(
            rx.hstack(
                meta_text(message.sender_display_name, font_weight="600"),
                meta_text(message.sent_at),
                spacing="2",
            ),
            body_text(message.content),
            spacing="0",
            align="start",
        ),
        spacing="2",
        align="start",
        padding_y="0.4rem",
        border_bottom="1px solid #ddd",
    )


def club_conversation_detail() -> rx.Component:
    return shell(
        page_title(ClubConversationDetailState.other_person_name),
        rx.cond(
            ClubConversationDetailState.error_message != "",
            rx.text(ClubConversationDetailState.error_message, color="red"),
        ),
        rx.foreach(ClubConversationDetailState.messages, _message_row),
        divider(),
        rx.form(
            rx.vstack(
                rx.text_area(
                    placeholder="Continue the conversation...",
                    value=ClubConversationDetailState.reply_draft,
                    on_change=ClubConversationDetailState.set_reply_draft,
                    rows="3",
                ),
                primary_button("Send", type="submit"),
                spacing="3",
            ),
            on_submit=ClubConversationDetailState.send_reply,
        ),
        rx.link("☞ Back to Communication", href="/communication", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["club_conversation_detail"]