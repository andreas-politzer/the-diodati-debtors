"""Add Book page — closes the CRUD loop for the library bounded context.

Owner selection is the same "temporary adapter" pattern as the
borrower picker on the dashboard: a plain dropdown of all users, until
auth_service exists and a book is simply owned by the logged-in user.
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
                rx.select(
                    LibraryState.user_options,
                    placeholder="Owner...",
                    name="owner_id",
                ),
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