"""Dashboard page — Grund-UI, Phase 2.

Shows the real book list from LibraryState (backed by book_service /
loan_service), not demo objects. No Goya/Easter-egg assets yet — the
Decorative-Assets-Gate (Implementation Specification.md) isn't cleared
until login, registration, and the full lend/return flow work
end-to-end, not just this manual dashboard.

Known limitations, tracked for later phases (see Roadmap.md backlog):
no search/filtering/pagination (fine at demo scale, not at 200+ books),
no owner-scoped "my library" view (shows all books system-wide), no
full Open Library metadata (deferred with ISBN lookup).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.library_state import BookView, LibraryState


def _borrower_picker(book_id: int, borrower_options: list[str]) -> rx.Component:
    """TEMPORARY ADAPTER — placeholder borrower selection until
    auth_service exists and lending happens as "the logged-in user".
    Isolated here deliberately so replacing it later touches only this
    function, never `_book_row`, `dashboard`, or LibraryState's public
    API.

    font_family is set explicitly to Font.system — Radix's rx.select
    otherwise inherits the page's base body font (Baskerville, serif)
    from global_style(), which is wrong for this system-chrome element.
    """
    return rx.select(
        borrower_options,
        placeholder="Lend to...",
        font_family=Font.system,
        font_size=Type.meta,
        on_change=lambda selected: LibraryState.lend_book(book_id, selected),
    )


def _book_row(book: BookView) -> rx.Component:
    return card(
        page_title(book.title),
        rx.cond(book.author, body_text(book.author)),
        rx.text(
            book.status,
            font_family=Font.system,
            font_size=Type.meta,
            color=Color.text_soft,
        ),
        rx.link(
    rx.hstack(
        rx.text("☞", font_size="2rem", line_height="1"),
        rx.text("View details", font_size=Type.body, font_family=Font.body),
        spacing="2",
        align="center",
    ),
    href=f"/book/{book.id}",
    margin_bottom="0.5rem",
    display="block",
),
        rx.cond(
            book.is_on_loan,
            primary_button(
                "Mark returned",
                on_click=lambda: LibraryState.return_book(book.active_loan_id),
            ),
            _borrower_picker(book.id, book.borrower_options),
        ),
        margin_bottom="1rem",
    )


def dashboard() -> rx.Component:
    return shell(
        page_title("The Library"),
        rx.link("☞ Add a book", href="/add-book", margin_bottom="1rem", display="block"),
        rx.cond(
            LibraryState.error_message != "",
            rx.text(
                LibraryState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        divider(),
        rx.foreach(LibraryState.books, _book_row),
        max_width="48rem",
    )


__all__ = ["dashboard"]