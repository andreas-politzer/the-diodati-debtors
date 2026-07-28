"""Add Book page — create mode of the shared BookForm, with two ways
to prefill it: Open Library title search, or ISBN lookup (inside the
form itself).
"""

from __future__ import annotations

import reflex as rx

from ..components.book_form import book_form
from ..components.book_search_panel import book_search_panel
from ..components.label import meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.book_detail_state import BookDetailState


def add_book() -> rx.Component:
    return shell(
        page_title("Add a book"),
        rx.hstack(
            rx.vstack(
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
                    BookDetailState.info_message != "",
                    rx.text(
                        BookDetailState.info_message,
                        font_family=Font.system,
                        font_size=Type.meta,
                    ),
                ),
                book_search_panel(),
                divider(),
                book_form(submit_label="Add book"),
                rx.link(
                    "☞ Back to library", href="/dashboard", margin_top="1rem", display="block"
                ),
                spacing="2",
                align="start",
                width="380px",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.image(src="/images/percy-shelley.jpg", width="100%"),
                meta_text(
                    "Percy Bysshe Shelley writing Prometheus Unbound — "
                    "posthumous portrait by Joseph Severn, 1845."
                ),
                width="100%",
                spacing="1",
            ),
            spacing="5",
            align="start",
        ),
        max_width="80rem",
    )


__all__ = ["add_book"]