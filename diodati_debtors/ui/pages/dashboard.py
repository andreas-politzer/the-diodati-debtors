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
from ..components.button import primary_button
from ..tokens import Border, Color, Font, Radius, Space, Type
from ...state.auth_state import AuthState
from ...state.group_state import GroupState
from ...state.library_state import LibraryState
from ...state.loan_activity_state import BorrowedLoanView, LoanActivityState
from ...state.organize_state import OrganizeState
from ...state.communication_state import CommunicationState
from ...models.enums import BookGenre


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


def _book_controls() -> rx.Component:
    return rx.flex(
        rx.vstack(
            meta_text("Search"),
            rx.input(
                placeholder="Search anything...",
                value=LibraryState.library_search_query,
                on_change=LibraryState.set_library_search_query,
                font_family=Font.system,
                font_size=Type.meta,
            ),
            rx.cond(
                (LibraryState.library_search_query != "")
                | (LibraryState.genre_filter != "All")
                | (LibraryState.availability_filter != "All")
                | (LibraryState.sort_option != "Recently added"),
                rx.link("✕ Clear filters", on_click=LibraryState.reset_book_controls, cursor="pointer"),
            ),
            spacing="1",
        ),
        rx.vstack(
            meta_text("Genre"),
            rx.select(
                ["All"] + [g.value for g in BookGenre],
                value=LibraryState.genre_filter,
                on_change=LibraryState.set_genre_filter,
                font_family=Font.system,
                font_size=Type.meta,
            ),
            spacing="1",
        ),
        rx.vstack(
            meta_text("Availability"),
            rx.select(
                ["All", "Available only"],
                value=LibraryState.availability_filter,
                on_change=LibraryState.set_availability_filter,
                font_family=Font.system,
                font_size=Type.meta,
            ),
            spacing="1",
        ),
        rx.vstack(
            meta_text("Sort"),
            rx.select(
                ["Recently added", "Title (A-Z)", "Author (A-Z)", "Availability", "Location"],
                value=LibraryState.sort_option,
                on_change=LibraryState.set_sort_option,
                font_family=Font.system,
                font_size=Type.meta,
            ),
            spacing="1",
        ),
        wrap="wrap",
        spacing="3",
        margin_bottom="1rem",
    )


def _loan_row(loan: BorrowedLoanView) -> rx.Component:
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
        rx.dialog.root(
            rx.dialog.trigger(primary_button("Mark returned", margin_top="0.5rem")),
            rx.dialog.content(
                rx.dialog.title("Mark as returned"),
                rx.vstack(
                    rx.text("How was the book's condition?"),
                    rx.select(
                        ["Skip rating", "Better than before", "Same condition", "Slightly worse", "Significantly worse"],
                        default_value="Skip rating",
                        on_change=LoanActivityState.set_return_condition_rating,
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            primary_button(
                                "Confirm return",
                                on_click=lambda: LoanActivityState.return_lent_out_book(loan.id),
                            )
                        ),
                        rx.dialog.close(primary_button("Cancel", type="button")),
                        spacing="2",
                    ),
                    spacing="3",
                ),
            ),
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
                    "Common Club Library",
                )
            ),
            rx.cond(
                LibraryState.active_tab == "borrowed",
                page_title("My Borrowed Books"),
                page_title("My Library"),
            ),
        ),
        rx.hstack(
            rx.vstack(
                meta_text(f"Logged in as {AuthState.current_user_display_name}", margin_bottom="0.5rem"),
                rx.link("☞ Add a book", href="/add-book", display="block"),
                rx.link("☞ Import Books", href="/import-books", margin_bottom="0.5rem", display="block"),
                rx.link("☞ Clubs", href="/clubs", display="block"),
                rx.link("☞ Bookmates", href="/members", display="block"),
                rx.link(
                    rx.hstack(
                        rx.text("☞ Organise"),
                        rx.cond(
                            OrganizeState.pending_count > 0,
                            rx.text(f"({OrganizeState.pending_count})", color=Color.accent, font_weight="700"),
                        ),
                        spacing="1",
                    ),
                    href="/organize",
                    display="block",
                ),
                rx.link(
                    rx.hstack(
                        rx.text("☞ Communication"),
                        rx.cond(
                            CommunicationState.unread_count > 0,
                            rx.text(f"({CommunicationState.unread_count})", color=Color.accent, font_weight="700"),
                        ),
                        spacing="1",
                    ),
                    href="/communication",
                    display="block",
                ),
                rx.link("☞ Ask the Librarian", href="/librarian", display="block"),
                spacing="2",
                align="start",
                width="230px",
                flex_shrink="0",
            ),
            rx.image(src="/images/trinity-library.jpg", width="100%", margin_left="1rem"),
            spacing="5",
            align="start",
            margin_bottom="1.5rem",
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
        rx.cond(
            LoanActivityState.error_message != "",
            rx.text(
                LoanActivityState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            LoanActivityState.info_message != "",
            meta_text(LoanActivityState.info_message),
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
        rx.cond(
            (LibraryState.active_tab == "personal") | (LibraryState.active_tab == "common"),
            _book_controls(),
        ),
        divider(),
        rx.cond(
            LibraryState.active_tab == "lent_out",
            rx.fragment(
                rx.vstack(
                    meta_text("Sort"),
                    rx.select(
                        ["Due date", "Loan date", "Book title", "Person"],
                        value=LoanActivityState.loan_sort_option,
                        on_change=LoanActivityState.set_loan_sort_option,
                        font_family=Font.system,
                        font_size=Type.meta,
                    ),
                    spacing="1",
                    margin_bottom="1rem",
                ),
                rx.cond(
                    LoanActivityState.lent_out_loans.length() > 0,
                    rx.grid(
                        rx.foreach(
                            LoanActivityState.lent_out_loans,
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
                    rx.vstack(
                        meta_text("Sort"),
                        rx.select(
                            ["Due date", "Loan date", "Book title", "Person"],
                            value=LoanActivityState.loan_sort_option,
                            on_change=LoanActivityState.set_loan_sort_option,
                            font_family=Font.system,
                            font_size=Type.meta,
                        ),
                        spacing="1",
                        margin_bottom="1rem",
                    ),
                    rx.cond(
                        LoanActivityState.borrowed_loans.length() > 0,
                        rx.grid(
                            rx.foreach(
                                LoanActivityState.borrowed_loans,
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
                            LoanActivityState.borrowed_loans,
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
        top_right=rx.vstack(
            rx.link(
                "☞ Log out",
                href="/",
                on_click=[AuthState.logout, GroupState.clear_selection],
            ),
            rx.link("☞ Profile", href="/profile"),
            spacing="1",
            align="start",
        ),
    )


__all__ = ["dashboard"]