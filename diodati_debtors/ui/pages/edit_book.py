"""Edit Book page — edit mode of the shared BookForm, prefilled from
BookDetailState.detail_book. Delete lives here too (with
confirmation), not in the book list — a deliberate, separate action
rather than something squeezed between lending buttons.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_form import book_form
from ..components.button import primary_button, warning_button
from ..components.label import meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.book_detail_state import BookDetailState


def edit_book() -> rx.Component:
    return shell(
        page_title("Edit book"),
        rx.cond(
            BookDetailState.error_message != "",
            rx.text(
                BookDetailState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            BookDetailState.detail_book,
            book_form(
                book_id=BookDetailState.detail_book.id,
                submit_label="Save changes",
            ),
        ),
        divider(),
        rx.cond(
            BookDetailState.pending_delete_book_id == BookDetailState.detail_book.id,
            rx.hstack(
                meta_text("Really delete this book? This cannot be undone."),
                warning_button(
                    "Yes, delete",
                    on_click=lambda: BookDetailState.delete_book(BookDetailState.detail_book.id),
                ),
                primary_button("Cancel", on_click=BookDetailState.cancel_delete),
                spacing="2",
            ),
            warning_button(
                "Delete this book",
                on_click=lambda: BookDetailState.confirm_delete(BookDetailState.detail_book.id),
            ),
        ),
        rx.link(
            "☞ Back to book",
            href=f"/book/{BookDetailState.book_id}",
            margin_top="1rem",
            display="block",
        ),
        max_width="32rem",
    )


__all__ = ["edit_book"]