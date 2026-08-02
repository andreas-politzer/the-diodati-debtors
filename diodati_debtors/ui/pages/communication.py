"""Communication hub — a pure entry point (per the 02.08. architecture
decision, project vault). Three cards: Personal Messages, Club Feed,
Global Board — each shows an unread count and the latest activity
preview. No content lives here directly; each card links to its own
dedicated page.
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import shell
from ...state.communication_state import CommunicationState, FeedPreview, PersonalMessagesPreview


def _unread_badge(count) -> rx.Component:
    return rx.cond(
        count > 0,
        rx.text(f"({count})", color="green", font_weight="700"),
    )


def _personal_messages_card() -> rx.Component:
    preview = CommunicationState.personal_messages
    return rx.vstack(
        rx.hstack(
            page_title("Personal Messages", font_size="1.1rem"),
            _unread_badge(CommunicationState.unread_personal_messages),
            spacing="2",
        ),
        rx.link(
            card(
                rx.cond(
                    preview.has_any,
                    rx.fragment(
                        meta_text(preview.other_person_name),
                        body_text(f'"{preview.last_message_preview}"'),
                        meta_text(preview.last_message_at),
                    ),
                    body_text("No conversations yet."),
                ),
                height="100%",
            ),
            href="/personal-messages",
            display="block",
            width="100%",
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _feed_card(title: str, preview: FeedPreview, unread_count, href: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            page_title(title, font_size="1.1rem"),
            _unread_badge(unread_count),
            spacing="2",
        ),
        rx.link(
            card(
                rx.cond(
                    preview.has_any,
                    rx.fragment(
                        meta_text(preview.author_name),
                        body_text(f'"{preview.content_preview}"'),
                        meta_text(preview.posted_at),
                    ),
                    body_text("No posts yet."),
                ),
                height="100%",
            ),
            href=href,
            display="block",
            width="100%",
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def communication() -> rx.Component:
    return shell(
        page_title("Communication", margin_bottom="1rem"),
        rx.cond(
            CommunicationState.error_message != "",
            rx.text(CommunicationState.error_message, color="red"),
        ),
        rx.grid(
            _personal_messages_card(),
            _feed_card(
                "Club Feed", CommunicationState.club_feed,
                CommunicationState.unread_club_feed, "/club-feed",
            ),
            _feed_card(
                "Global Board", CommunicationState.global_board,
                CommunicationState.unread_global_board, "/board",
            ),
            columns="repeat(auto-fit, minmax(220px, 1fr))",
            gap="1rem",
            width="100%",
        ),
        rx.center(
            rx.vstack(
                rx.image(src="/images/mailman_british.jpg", max_width="320px", margin_top="2rem"),
                meta_text(
                    'William Alexander, "Postman", in Picturesque Representations '
                    "of the Dress and Manners of the English, 1814. Public domain, "
                    "via The New York Public Library."
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="60rem",
    )


__all__ = ["communication"]