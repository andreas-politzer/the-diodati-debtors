"""Book action bar — lending/borrowing actions. Edit/Delete live on
Book Detail / Edit pages. "Lend to a contact" is a slim link here too
(only for own, available books). Both "Request to borrow" and "Mark
returned" open a small dialog instead of being instant/always-visible
— keeps the card itself lean.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from .label import meta_text
from ...state.library_state import BookView, LibraryState


def _request_dialog(book: BookView) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            primary_button("Request to borrow", on_click=lambda: LibraryState.open_request_dialog(book.id))
        ),
        rx.dialog.content(
            rx.dialog.title("Request to borrow"),
            rx.vstack(
                rx.text("Preferred loan period:"),
                rx.radio(
                    ["Standard (14 days)", "Custom"],
                    value=LibraryState.request_period_choice,
                    on_change=LibraryState.set_request_period_choice,
                ),
                rx.cond(
                    LibraryState.request_period_choice == "Custom",
                    rx.vstack(
                        rx.text("Until:"),
                        rx.input(
                            type="date",
                            value=LibraryState.request_custom_due_date,
                            on_change=LibraryState.set_request_custom_due_date,
                        ),
                        spacing="1",
                    ),
                ),
                rx.input(
                    placeholder="Note (optional) — e.g. I'm on vacation for 3 weeks",
                    value=LibraryState.request_note,
                    on_change=LibraryState.set_request_note,
                ),
                rx.hstack(
                    rx.dialog.close(
                        primary_button("Send request", on_click=LibraryState.request_to_borrow)
                    ),
                    rx.dialog.close(primary_button("Cancel", type="button")),
                    spacing="2",
                ),
                spacing="3",
            ),
        ),
    )


def _return_dialog(book: BookView) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(primary_button("Mark returned")),
        rx.dialog.content(
            rx.dialog.title("Mark as returned"),
            rx.vstack(
                rx.text("How was the book's condition?"),
                rx.select(
                    ["Skip rating", "Better than before", "Same condition", "Slightly worse", "Significantly worse"],
                    default_value="Skip rating",
                    on_change=LibraryState.set_return_condition_rating,
                ),
                rx.hstack(
                    rx.dialog.close(
                        primary_button("Confirm return", on_click=lambda: LibraryState.return_book(book))
                    ),
                    rx.dialog.close(primary_button("Cancel", type="button")),
                    spacing="2",
                ),
                spacing="3",
            ),
        ),
    )


def book_action_bar(book: BookView) -> rx.Component:
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