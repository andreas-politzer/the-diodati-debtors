"""Add Book page — create mode of the shared BookForm."""

from __future__ import annotations

import reflex as rx

from ..components.book_form import book_form
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
        rx.cond(
            LibraryState.info_message != "",
            rx.text(
                LibraryState.info_message,
                font_family=Font.system,
                font_size=Type.meta,
            ),
        ),
        book_form(submit_label="Add book"),
        rx.link(
            "☞ Back to library", href="/dashboard", margin_top="1rem", display="block"
        ),
        max_width="32rem",
    )


__all__ = ["add_book"]