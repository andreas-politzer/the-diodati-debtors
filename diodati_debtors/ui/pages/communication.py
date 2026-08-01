"""Communication hub — an inbox/work-list of ongoing bibliothekarisch
processes (Borrowing Inquiries, Club Conversations), plus links to
the two book-independent Post projections (Club Feed, Global Board).

Per ChatGPT's review (01.08., project vault): this page is a work
list, not a messenger. The process is primary, the conversation is
only its detail view — deliberately no chat/bubble/contact-list
visual language here. Rows render in a responsive grid (auto-fill,
minimum card width) — same pattern as the book grid, not one row per
full page width.
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.communication_state import CommunicationRow, CommunicationState


def _row(row: CommunicationRow) -> rx.Component:
    href = rx.cond(
        row.process_type == "borrowing_inquiry",
        f"/borrowing-inquiry/{row.process_id}",
        f"/club-conversation/{row.process_id}",
    )
    preview_prefix = rx.cond(row.last_message_is_own, "You: ", "")
    return rx.link(
        card(
            rx.hstack(
                body_text(row.other_person_name),
                meta_text(row.label),
                spacing="2",
            ),
            meta_text(row.subject),
            body_text(f'{preview_prefix}"{row.last_message_preview}"'),
            meta_text(row.last_message_at),
            height="100%",
        ),
        href=href,
        display="block",
    )


def communication() -> rx.Component:
    return shell(
        page_title("Communication", margin_bottom="1rem"),
        rx.cond(
            CommunicationState.error_message != "",
            rx.text(CommunicationState.error_message, color="red"),
        ),
        rx.cond(
            CommunicationState.rows.length() > 0,
            rx.grid(
                rx.foreach(CommunicationState.rows, _row),
                columns="repeat(auto-fill, minmax(220px, 1fr))",
                gap="1rem",
                width="100%",
            ),
            body_text("No ongoing conversations yet."),
        ),
        divider(),
        rx.link("☞ Club Feed", href="/club-feed", margin_top="1rem", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Global Board", href="/board", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="80rem",
    )


__all__ = ["communication"]