"""Member detail page — a read-only view of one member's personal
library, reusing the exact same book_row component as the dashboard.
Same rendering, same actions (Request to borrow on their books) — only
the data source (one specific member's catalogue) differs.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_row import book_row
from ..components.label import page_title
from ..components.shell import shell
from ...state.library_state import LibraryState


def member_detail() -> rx.Component:
    return shell(
        page_title(f"{LibraryState.viewing_member_name}'s Library"),
        rx.foreach(LibraryState.member_books, book_row),
        rx.link("☞ Back to members", href="/members", margin_top="1rem", display="block"),
        max_width="48rem",
    )


__all__ = ["member_detail"]