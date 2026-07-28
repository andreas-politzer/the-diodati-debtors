"""Book action bar — lending/borrowing actions. Edit/Delete live on
Book Detail / Edit pages. "Lend to a contact" is a slim link here too
(only for own, available books). Both "Request to borrow" and "Mark
returned" open a small dialog instead of being instant/always-visible
— keeps the card itself lean.

Accepts any book-like object (LibraryState's BookView or
MemberLibraryState's MemberBookView both work) — no State import here,
same duck-typing approach as book_row.py.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from .label import meta_text
from ...state.loan_activity_state import LoanActivityState
from ...state.library_state import LibraryState


def _request_dialog(book) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            primary_button("Request to borrow", on_click=lambda: LoanActivityState.open_request_dialog(book.id))
        ),
        rx.dialog.content(
            rx.dialog.title("Request to borrow"),
            rx.vstack(
                rx.text("Preferred loan period:"),
                rx.radio(
                    ["Standard (14 days)", "Custom"],
                    value=LoanActivityState.request_period_choice,
                    on_change=LoanActivityState.set_request_period_choice,
                ),
                rx.cond(
                    LoanActivityState.request_period_choice == "Custom",
                    rx.vstack(
                        rx.text("Until:"),
                        rx.input(
                            type="date",
                            value=LoanActivityState.request_custom_due_date,
                            on_change=LoanActivityState.set_request_custom_due_date,
                        ),
                        spacing="1",
                    ),
                ),
                rx.input(
                    placeholder="Note (optional) — e.g. I'm on vacation for 3 weeks",
                    value=LoanActivityState.request_note,
                    on_change=LoanActivityState.set_request_note,
                ),
                rx.hstack(
                    rx.dialog.close(
                        primary_button("Send request", on_click=LoanActivityState.request_to_borrow)
                    ),
                    rx.dialog.close(primary_button("Cancel", type="button")),
                    spacing="2",
                ),
                spacing="3",
            ),
        ),
    )


def _return_dialog(book) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(primary_button("Mark returned")),
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
                            on_click=lambda: [LoanActivityState.return_book(book), LibraryState.load_books],
                        )
                    ),
                    rx.dialog.close(primary_button("Cancel", type="button")),
                    spacing="2",
                ),
                spacing="3",
            ),
        ),
    )


def book_action_bar(book) -> rx.Component:
    return rx.cond(
        book.is_own_book,
        rx.cond(
            book.is_on_loan,
            _return_dialog(book),
            rx.vstack(
                meta_text("Your book"),
                rx.link("☞ Lend to a contact", href="/lend-to-contact"),
                spacing="1",
            ),
        ),
        rx.cond(
            book.is_on_loan,
            meta_text("Currently on loan"),
            rx.cond(
                book.has_pending_request,
                meta_text("Request sent — waiting for approval"),
                _request_dialog(book),
            ),
        ),
    )


__all__ = ["book_action_bar"]