"""Book action bar — lending/borrowing actions only. Edit/Delete now
live on the Book Detail / Edit pages instead (Andy's request: keep
the list view lean as it grows more crowded)."""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from .label import meta_text
from ...state.library_state import BookView, LibraryState


def book_action_bar(book: BookView) -> rx.Component:
    return rx.cond(
        book.is_own_book,
        rx.cond(
            book.is_on_loan,
            primary_button(
                "Mark returned",
                on_click=lambda: LibraryState.return_book(book),
            ),
            meta_text("Your book"),
        ),
        rx.cond(
            book.is_on_loan,
            meta_text("Currently on loan"),
            rx.cond(
                book.has_pending_request,
                meta_text("Request sent — waiting for approval"),
                primary_button(
                    "Request to borrow",
                    on_click=lambda: LibraryState.request_to_borrow(book.id),
                ),
            ),
        ),
    )


__all__ = ["book_action_bar"]