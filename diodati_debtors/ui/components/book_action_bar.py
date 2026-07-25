"""Book action bar — lending/borrowing actions. Edit/Delete live on
Book Detail / Edit pages. "Lend to a contact" is a slim link here too
(only for own, available books) — the actual workflow lives on its own
page (/lend-to-contact).
"""

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
            rx.vstack(
                rx.select(
                    ["Skip rating", "Better than before", "Same condition", "Slightly worse", "Significantly worse"],
                    default_value="Skip rating",
                    on_change=LibraryState.set_return_condition_rating,
                ),
                primary_button(
                    "Mark returned",
                    on_click=lambda: LibraryState.return_book(book),
                ),
                spacing="2",
            ),
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
                primary_button(
                    "Request to borrow",
                    on_click=lambda: LibraryState.request_to_borrow(book.id),
                ),
            ),
        ),
    )


__all__ = ["book_action_bar"]