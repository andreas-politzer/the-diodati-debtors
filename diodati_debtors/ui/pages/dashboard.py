"""Dashboard page — "What books can I access right now?"

Personal Library / Common Club Library as tabs, one shared list
component (book_row) — data source changes, presentation stays
identical. The Common Club Library tab owns a club switcher; this is
the one place in the app where the active club context is chosen
(GitHub-repo / Slack-workspace style) — Clubs page and Members page no
longer duplicate this selection.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_row import book_row
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


def _club_switcher() -> rx.Component:
    return rx.vstack(
        meta_text("Current club"),
        rx.select(
            GroupState.group_options,
            placeholder="Switch club...",
            font_family=Font.system,
            font_size=Type.meta,
            on_change=lambda selected: [
                GroupState.switch_group(selected),
                LibraryState.load_books,
            ],
        ),
        spacing="1",
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
                    "Common Club Library",
                )
            ),
            page_title("My Library"),
        ),
        meta_text(f"Logged in as {AuthState.current_user_display_name}"),
        rx.link("☞ Add a book", href="/add-book", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Clubs", href="/clubs", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Members", href="/members", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Organize", href="/organize", margin_bottom="0.5rem", display="block"),
        rx.link(
            "☞ Log out",
            href="/",
            on_click=[AuthState.logout, GroupState.clear_selection],
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
        rx.cond(
            LibraryState.info_message != "",
            meta_text(LibraryState.info_message),
        ),
        rx.hstack(
            _tab_button("Personal Library", "personal"),
            _tab_button("Common Club Library", "common"),
            spacing="3",
            margin_bottom="1rem",
        ),
        rx.cond(
            LibraryState.active_tab == "common",
            rx.cond(
                GroupState.current_group_id == "",
                rx.cond(
                    GroupState.has_groups,
                    rx.fragment(
                        body_text("You haven't selected a club yet."),
                        meta_text("Choose one from the dropdown above."),
                    ),
                    rx.fragment(
                        body_text("You're not a member of any club yet."),
                        rx.link(
                            "☞ Browse or found a club",
                            href="/clubs",
                            margin_top="0.5rem",
                            display="block",
                        ),
                    ),
                ),
                rx.cond(
                    LibraryState.books.length() > 0,
                    rx.foreach(LibraryState.books, book_row),
                    body_text("This club doesn't have any books yet."),
                ),
            ),
            rx.cond(
                LibraryState.books.length() > 0,
                rx.foreach(LibraryState.books, book_row),
                rx.fragment(
                    body_text("You don't have any books in your library yet."),
                    body_text(
                        'Click "Add a book" and start building your personal library.'
                    ),
                ),
            ),
        ),
        max_width="48rem",
    )


__all__ = ["dashboard"]