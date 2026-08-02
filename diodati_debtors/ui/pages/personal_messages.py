"""Personal Messages — the contact-oriented overview of all Club
Conversations (per the 02.08. UX decision, project vault): one entry
per person, like WhatsApp. Fixed-height box with internal scrolling —
the page itself never grows, only the list within it does.
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import shell
from ...state.personal_messages_state import PersonalMessageEntry, PersonalMessagesState


def _entry_row(entry: PersonalMessageEntry) -> rx.Component:
    return rx.link(
        card(
            rx.hstack(
                body_text(entry.other_person_name, font_weight="600"),
                rx.cond(
                    entry.unread_count > 0,
                    rx.text(f"({entry.unread_count})", color="green", font_weight="700"),
                ),
                spacing="2",
            ),
            meta_text(f'"{entry.last_message_preview}"'),
            meta_text(entry.last_message_at),
            margin_bottom="0.5rem",
        ),
        href=f"/club-conversation/{entry.conversation_id}",
        display="block",
    )


def personal_messages() -> rx.Component:
    return shell(
        page_title("Personal Messages", margin_bottom="1rem"),
        rx.cond(
            PersonalMessagesState.error_message != "",
            rx.text(PersonalMessagesState.error_message, color="red"),
        ),
        rx.input(
            placeholder="Search by name...",
            value=PersonalMessagesState.search_query,
            on_change=PersonalMessagesState.set_search_query,
            margin_bottom="0.75rem",
        ),
        rx.box(
            rx.cond(
                PersonalMessagesState.filtered_entries.length() > 0,
                rx.foreach(PersonalMessagesState.filtered_entries, _entry_row),
                body_text("No conversations yet."),
            ),
            height="400px",
            overflow_y="auto",
            width="100%",
        ),
        rx.link("☞ Back to Communication", href="/communication", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["personal_messages"]