"""Dashboard page — Common/Personal Library as tabs, one shared list
component: data source changes, presentation stays identical.

No hard redirect to /clubs — Personal Library must work with zero
clubs (Domain Model v2, principle 1). The Common tab shows an inline
prompt instead of blocking the page when no club is selected.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Border, Color, Font, Radius, Space, Type
from ...state.auth_state import AuthState
from ...state.group_state import GroupState
from ...state.library_state import LibraryState


def _tab_button(label: str, tab_key: str) -> rx.Component:
    return rx.button(
        label,
        on_click=lambda: LibraryState.set_tab(tab_key),
        background_color=rx.cond(
            LibraryState.active_tab == tab_key, Color.accent, Color.text
        ),
        color=Color.accent_contrast,
        font_family=Font.system,
        font_size=Type.meta,
        font_weight="600",
        border=Border.hairline,
        border_radius=Radius.max,
        padding_x=Space.md,
        padding_y=Space.sm,
        cursor="pointer",
    )


def _borrower_picker(book_id, borrower_options) -> rx.Component:
    """TEMPORARY ADAPTER — placeholder borrower selection until
    lending happens as "the logged-in user". Isolated here deliberately
    so replacing it later touches only this function.
    """
    return rx.select(
        borrower_options,
        placeholder="Lend to...",
        font_family=Font.system,
        font_size=Type.meta,
        on_change=lambda selected: LibraryState.lend_book(book_id, selected),
    )


def _book_row(book) -> rx.Component:
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
        rx.cond(
            LibraryState.active_tab == "common",
            page_title(
                rx.cond(
                    GroupState.current_group_id != "",
                    GroupState.current_group_name,
                    "Common Library",
                )
            ),
            page_title("My Library"),
        ),
        meta_text(f"Logged in as {AuthState.current_user_display_name}"),
        rx.link("☞ Add a book", href="/add-book", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Your clubs", href="/clubs", margin_bottom="0.5rem", display="block"),
        rx.link(
            "☞ Log out",
            href="/",
            on_click=AuthState.logout,
            margin_bottom="1rem",
            display="block",
        ),
        rx.cond(
            LibraryState.error_message != "",
            rx.text(
                LibraryState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.hstack(
            _tab_button("Personal Library", "personal"),
            _tab_button("Common Library", "common"),
            spacing="3",
            margin_bottom="1rem",
        ),
        divider(),
        rx.cond(
            (LibraryState.active_tab == "common") & (GroupState.current_group_id == ""),
            rx.fragment(
                body_text("Select or found a club to see its shared library."),
                rx.link(
                    "☞ Go to your clubs", href="/clubs", margin_top="0.5rem", display="block"
                ),
            ),
            rx.foreach(LibraryState.books, _book_row),
        ),
        max_width="48rem",
    )


__all__ = ["dashboard"]