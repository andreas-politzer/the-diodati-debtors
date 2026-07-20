"""Shared book-row rendering — used by the dashboard (Personal/Common
Library tabs) and the Members detail page. Same card, same action
logic, regardless of where the book list came from — the data source
changes, the presentation stays identical (same principle as the
dashboard tabs).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..tokens import Color, Font, Type
from ...state.library_state import LibraryState, BookView


def _book_action(book: BookView) -> rx.Component:
    return rx.cond(
        book.is_own_book,
        rx.cond(
            book.is_on_loan,
            primary_button(
                "Mark returned",
                on_click=lambda: LibraryState.return_book(book),
            ),
            meta_text("Your book"),
        ),
        rx.cond(
            book.is_on_loan,
            meta_text("Currently on loan"),
            rx.cond(
                book.has_pending_request,
                meta_text("Request sent — waiting for approval"),
                primary_button(
                    "Request to borrow",
                    on_click=lambda: LibraryState.request_to_borrow(book.id),
                ),
            ),
        ),
    )


def book_row(book: BookView) -> rx.Component:
    return card(
        page_title(book.title),
        rx.cond(book.author, body_text(book.author)),
        rx.cond(book.location, meta_text(f"Location: {book.location}")),
        rx.cond(~book.is_own_book, meta_text(f"Owned by {book.owner_name}")),
        rx.text(
            book.status,
            font_family=Font.system,
            font_size=Type.meta,
            color=Color.text_soft,
        ),
        rx.link(
            rx.hstack(
                rx.text("☞", font_size="2rem", line_height="1"),
                rx.text("View details", font_size=Type.body, font_family=Font.body),
                spacing="2",
                align="center",
            ),
            href=f"/book/{book.id}",
            margin_bottom="0.5rem",
            display="block",
        ),
        _book_action(book),
        margin_bottom="1rem",
    )


__all__ = ["book_row"]