"""Shared book-row rendering — used by the dashboard and the Members
detail page. Pure presentation; all workflow actions live in
BookActionBar.
"""

from __future__ import annotations

import reflex as rx

from .book_action_bar import book_action_bar
from .card import card
from .label import body_text, meta_text, page_title
from ..tokens import Color, Font, Type
from ...state.library_state import BookView


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
        book_action_bar(book),
        margin_bottom="1rem",
    )


__all__ = ["book_row"]