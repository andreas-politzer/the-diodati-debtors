"""Edit Book page — edit mode of the shared BookForm, prefilled via
LibraryState._populate_form_from_detail. Same search/ISBN-lookup
options as Add Book — the form is a reusable editing surface,
regardless of what feeds it.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_form import book_form
from ..components.book_search_panel import book_search_panel
from ..components.label import page_title
from ..components.shell import divider, shell
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
            LibraryState.info_message != "",
            rx.text(
                LibraryState.info_message,
                font_family=Font.system,
                font_size=Type.meta,
            ),
        ),
        book_search_panel(),
        divider(),
        rx.cond(
            LibraryState.detail_book,
            book_form(book_id=LibraryState.detail_book.id, submit_label="Save changes"),
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