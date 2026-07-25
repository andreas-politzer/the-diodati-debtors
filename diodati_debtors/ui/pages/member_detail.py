"""Member detail page — a read-only view of one member's personal
library, reusing the exact same book_row component as the dashboard.
Same rendering, same actions (Request to borrow on their books) — only
the data source (one specific member's catalogue) differs.

Books render in a responsive grid — auto-fill with a minimum card
width, so 2-4 columns appear depending on screen width, never a fixed
column count.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_row import book_row
from ..components.label import meta_text, page_title
from ..components.shell import shell
from ...state.library_state import LibraryState


def member_detail() -> rx.Component:
    return shell(
        page_title(f"{LibraryState.viewing_member_name}'s Library"),
        meta_text(f"Reliability: {LibraryState.viewing_member_reliability}"),
        meta_text(f"Book Care: {LibraryState.viewing_member_book_care}"),
        rx.grid(
            rx.foreach(LibraryState.member_books, book_row),
            columns="repeat(auto-fill, minmax(220px, 1fr))",
            gap="1rem",
            width="100%",
        ),
        rx.link("☞ Back to members", href="/members", margin_top="1rem", display="block"),
        max_width="80rem",
    )


__all__ = ["member_detail"]