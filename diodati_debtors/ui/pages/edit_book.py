"""Edit Book page — edit mode of the shared BookForm, pre-filled from
LibraryState.detail_book (loaded via the same load_book_detail used by
the book detail page — same dynamic route segment name, book_id).
"""

from __future__ import annotations

import reflex as rx

from ..components.book_form import book_form
from ..components.label import page_title
from ..components.shell import shell
from ..tokens import Color, Font, Type
from ...state.library_state import LibraryState


def edit_book() -> rx.Component:
    return shell(
        page_title("Edit book"),
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
            LibraryState.detail_book,
            book_form(
                book_id=LibraryState.detail_book.id,
                initial_title=LibraryState.detail_book.title,
                initial_author=rx.cond(LibraryState.detail_book.author, LibraryState.detail_book.author, ""),
                initial_isbn=rx.cond(LibraryState.detail_book.isbn, LibraryState.detail_book.isbn, ""),
                initial_location=rx.cond(LibraryState.detail_book.location, LibraryState.detail_book.location, ""),
                submit_label="Save changes",
            ),
        ),
        rx.link(
            "☞ Back to book",
            href=f"/book/{LibraryState.book_id}",
            margin_top="1rem",
            display="block",
        ),
        max_width="32rem",
    )


__all__ = ["edit_book"]