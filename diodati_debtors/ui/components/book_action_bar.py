"""Book action bar — all workflow-specific actions for one book:
request/return, plus owner-only edit/delete with confirmation.

Extracted from book_row per the Struktur.md guideline ("extract once
actions grow beyond the original two") — book_row now stays pure
presentation, this owns all decision logic.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button, warning_button
from .label import meta_text
from ...state.library_state import BookView, LibraryState


def _delete_confirm(book: BookView) -> rx.Component:
    return rx.vstack(
        meta_text("Delete this book? This cannot be undone."),
        rx.hstack(
            warning_button("Delete", on_click=lambda: LibraryState.delete_book(book.id)),
            primary_button("Cancel", on_click=LibraryState.cancel_delete),
            spacing="2",
        ),
        spacing="1",
    )


def book_action_bar(book: BookView) -> rx.Component:
    lending_action = rx.cond(
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

    owner_actions = rx.cond(
        book.is_own_book,
        rx.hstack(
            rx.link("☞ Edit", href=f"/book/{book.id}/edit"),
            rx.cond(
                LibraryState.pending_delete_book_id == book.id,
                _delete_confirm(book),
                primary_button(
                    "Delete", on_click=lambda: LibraryState.confirm_delete(book.id)
                ),
            ),
            spacing="3",
            margin_top="0.5rem",
        ),
    )

    return rx.vstack(lending_action, owner_actions, spacing="2", align="start")


__all__ = ["book_action_bar"]