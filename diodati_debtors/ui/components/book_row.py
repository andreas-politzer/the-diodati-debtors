"""Shared book-row rendering — used by the dashboard (LibraryState's
BookView) and the Members detail page (MemberLibraryState's
MemberBookView). Both dataclasses share the same shape by design, so
this stays a pure presentation function with no State import at all —
duck-typed intentionally, since this is a UI component, not a
State-to-State coupling concern.

Pure presentation; all workflow actions live in BookActionBar.
Compact by design: sized to fit multiple columns in a responsive grid
(see the library pages' grid wrapper), not a full-width single-column
row.
"""

from __future__ import annotations

import reflex as rx

from .book_action_bar import book_action_bar
from .card import card
from .label import body_text, meta_text, page_title
from ..tokens import Color, Font, Type


def book_row(book) -> rx.Component:
    return card(
        page_title(book.title, font_size="1.1rem"),
        rx.cond(book.author, body_text(book.author)),
        rx.cond(book.location, meta_text(f"Location: {book.location}")),
        rx.cond(book.genre, meta_text(f"Genre: {book.genre}")),
        rx.cond(~book.is_own_book, meta_text(f"Owned by {book.owner_name}")),
        rx.text(
            book.status,
            font_family=Font.system,
            font_size=Type.meta,
            color=Color.text_soft,
        ),
        rx.link(
            rx.hstack(
                rx.text("☞", font_size="1.5rem", line_height="1"),
                rx.text("View details", font_size=Type.meta, font_family=Font.body),
                spacing="2",
                align="center",
            ),
            href=f"/book/{book.id}",
            margin_bottom="0.5rem",
            display="block",
        ),
        book_action_bar(book),
        height="100%",
    )


__all__ = ["book_row"]