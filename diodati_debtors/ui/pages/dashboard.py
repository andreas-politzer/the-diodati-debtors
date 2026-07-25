"""Dashboard page — "What can I access right now?"

Two tabs: Personal Library, Common Club Library, plus My Borrowed
Books as a third. My Lent-Out Books moved to its own page (too
prominent as a fourth tab, per Andy's feedback) — same pattern as
Reviews/Synopsis/Discussion, linked from the nav instead.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_row import book_row
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Border, Color, Font, Radius, Space, Type
from ...state.auth_state import AuthState
from ...state.group_state import GroupState
from ...state.library_state import BorrowedLoanView, LibraryState
from ...state.organize_state import OrganizeState


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


def _loan_row(loan: BorrowedLoanView) -> rx.Component:
    """One row in My Borrowed Books — Vanitas motifs per the Design
    Contract: skull for overdue, hourglass for due-soon, no icon at
    all when everything's fine (deliberate restraint over a third,
    invented symbol).
    """
    return card(
        page_title(loan.book_title, font_size="1.1rem"),
        meta_text(f"Owned by {loan.owner_name}"),
        meta_text(f"Loaned {loan.loan_date}, due {loan.due_date}"),
        rx.cond(
            loan.is_overdue,
            rx.text("☠ Overdue", font_weight="700"),
            rx.cond(loan.is_due_soon, rx.text("⏳ Due soon"), rx.fragment()),
        ),
        rx.cond(loan.is_active == False, meta_text(f"Returned {loan.return_date}")),
        rx.link("☞ View details", href=f"/book/{loan.book_id}", margin_top="0.5rem", display="block"),
        margin_bottom="1rem",
    )

def _lent_out_row(loan) -> rx.Component:
    return card(
        page_title(loan.book_title, font_size="1.1rem"),
        meta_text(f"Lent to {loan.borrower_name}"),
        meta_text(f"Loaned {loan.loan_date}, due {loan.due_date}"),
        rx.cond(
            loan.is_overdue,
            rx.text("☠ Overdue", font_weight="700"),
            rx.cond(loan.is_due_soon, rx.text("⏳ Due soon"), rx.fragment()),
        ),
        rx.link("☞ View details", href=f"/book/{loan.book_id}", margin_top="0.5rem", display="block"),
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
            rx.cond(
                LibraryState.active_tab == "borrowed",
                page_title("My Borrowed Books"),
                page_title("My Library"),
            ),
        ),
        meta_text(f"Logged in as {AuthState.current_user_display_name}", margin_bottom="1rem"),
        rx.link("☞ Add a book", href="/add-book", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Clubs", href="/clubs", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Bookmates", href="/members", margin_bottom="0.5rem", display="block"),
        rx.link(
            rx.hstack(
                rx.text("☞ Organize"),
                rx.cond(
                    OrganizeState.pending_count > 0,
                    rx.text(f"({OrganizeState.pending_count})", color=Color.accent, font_weight="700"),
                ),
                spacing="1",
            ),
            href="/organize",
            margin_bottom="0.5rem",
            display="block",
        ),
        rx.link("☞ Communication", href="/communication", margin_bottom="0.5rem", display="block"),
        
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
            _tab_button("My Borrowed Books", "borrowed"),
            _tab_button("My Lent-Out Books", "lent_out"),
            spacing="3",
            margin_bottom="1rem",
        ),
        rx.cond(LibraryState.active_tab == "common", _club_switcher()),
        divider(),
        rx.cond(
            LibraryState.active_tab == "lent_out",
            rx.fragment(
                rx.cond(
                    LibraryState.lent_out_loans.length() > 0,
                    rx.grid(
                        rx.foreach(
                            LibraryState.lent_out_loans,
                            lambda loan: rx.cond(loan.is_active, _lent_out_row(loan), rx.fragment()),
                        ),
                        columns="repeat(auto-fill, minmax(220px, 1fr))",
                        gap="1rem",
                        width="100%",
                    ),
                    body_text("You haven't lent out any books right now."),
                ),
                rx.link(
                    "☞ My Lent-Out History",
                    href="/lent-out-history",
                    margin_top="1rem",
                    display="block",
                ),
            ),
            rx.cond(
                LibraryState.active_tab == "borrowed",
                rx.fragment(
                    page_title("Currently Borrowed"),
                    rx.cond(
                        LibraryState.borrowed_loans.length() > 0,
                        rx.grid(
                            rx.foreach(
                                LibraryState.borrowed_loans,
                                lambda loan: rx.cond(loan.is_active, _loan_row(loan), rx.fragment()),
                            ),
                            columns="repeat(auto-fill, minmax(220px, 1fr))",
                            gap="1rem",
                            width="100%",
                        ),
                        body_text("You haven't borrowed any books right now."),
                    ),
                    divider(),
                    page_title("Borrow History"),
                    rx.grid(
                        rx.foreach(
                            LibraryState.borrowed_loans,
                            lambda loan: rx.cond(loan.is_active == False, _loan_row(loan), rx.fragment()),
                        ),
                        columns="repeat(auto-fill, minmax(220px, 1fr))",
                        gap="1rem",
                        width="100%",
                    ),
                ),
                rx.cond(
                    (LibraryState.active_tab == "common")
                    & (GroupState.current_group_id == ""),
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
                        rx.grid(
                            rx.foreach(LibraryState.books, book_row),
                            columns="repeat(auto-fill, minmax(220px, 1fr))",
                            gap="1rem",
                            width="100%",
                        ),
                        rx.cond(
                            LibraryState.active_tab == "common",
                            body_text("This club doesn't have any books yet."),
                            rx.fragment(
                                body_text("You don't have any books in your library yet."),
                                body_text(
                                    'Click "Add a book" and start building your personal library.'
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        max_width="80rem",
        top_right=rx.link(
            "☞ Log out",
            href="/",
            on_click=[AuthState.logout, GroupState.clear_selection],
        ),
    )


__all__ = ["dashboard"]