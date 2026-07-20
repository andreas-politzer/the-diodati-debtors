"""Add Book page — adds to the logged-in user's own catalogue.

No owner picker: since this always means "add a book to MY personal
library", the owner is the logged-in user, never a choice. (Earlier
versions of this page had an owner dropdown, left over from before
auth_service existed — removed now that it's genuinely redundant.)
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import page_title
from ..components.shell import shell
from ..tokens import Color, Font, Type
from ...state.library_state import LibraryState


def add_book() -> rx.Component:
    return shell(
        page_title("Add a book"),
        rx.cond(
            LibraryState.error_message != "",
            rx.text(
                LibraryState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.form(
            rx.vstack(
                rx.input(placeholder="Title", name="title", required=True),
                rx.input(placeholder="Author", name="author"),
                rx.input(placeholder="ISBN", name="isbn"),
                rx.input(placeholder="Location (optional)", name="location"),
                primary_button("Add book", type="submit"),
                spacing="3",
            ),
            on_submit=LibraryState.submit_new_book,
            reset_on_submit=True,
        ),
        rx.link(
            "☞ Back to library", href="/dashboard", margin_top="1rem", display="block"
        ),
        max_width="32rem",
    )


__all__ = ["add_book"]