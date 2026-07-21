"""My Borrowed Books page — Currently Borrowed and Borrow History as
two sections over the same data, split by is_active (not two separate
queries — see LibraryState.load_borrowed_books).

Vanitas motifs, per the Design Contract: a skull for overdue loans, an
hourglass for loans due within 3 days — historically paired symbols
(memento mori), not invented icons. Loans that are simply fine get no
icon at all — deliberate restraint over a third, manufactured symbol.
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.library_state import BorrowedLoanView, LibraryState


def _loan_row(loan: BorrowedLoanView) -> rx.Component:
    return card(
        page_title(loan.book_title),
        meta_text(f"Owned by {loan.owner_name}"),
        meta_text(f"Loaned {loan.loan_date}, due {loan.due_date}"),
        rx.cond(
            loan.is_overdue,
            rx.text("☠ Overdue", font_weight="700"),
            rx.cond(
                loan.is_due_soon,
                rx.text("⏳ Due soon"),
                rx.fragment(),
            ),
        ),
        rx.cond(
            ~loan.is_active,
            meta_text(f"Returned {loan.return_date}"),
        ),
        margin_bottom="1rem",
    )


def borrowed_books() -> rx.Component:
    active_loans = LibraryState.borrowed_loans  # filtered below in each cond
    return shell(
        page_title("My Borrowed Books"),
        rx.cond(
            LibraryState.error_message != "",
            rx.text(
                LibraryState.error_message,
                font_family="inherit",
            ),
        ),
        page_title("Currently Borrowed"),
        rx.cond(
            LibraryState.borrowed_loans.length() > 0,
            rx.fragment(
                rx.foreach(
                    LibraryState.borrowed_loans,
                    lambda loan: rx.cond(loan.is_active, _loan_row(loan), rx.fragment()),
                )
            ),
            body_text("You haven't borrowed any books right now."),
        ),
        divider(),
        page_title("Borrow History"),
        rx.foreach(
            LibraryState.borrowed_loans,
            lambda loan: rx.cond(~loan.is_active, _loan_row(loan), rx.fragment()),
        ),
        rx.link(
            "☞ Back to library", href="/dashboard", margin_top="1rem", display="block"
        ),
        max_width="40rem",
    )


__all__ = ["borrowed_books"]