"""Shared Add/Edit Book form. One component, one handler
(BookDetailState.submit_book_form). Fields are controlled (value=
bound to BookDetailState.form_*) rather than default_value/
uncontrolled — this is what makes the ISBN lookup button able to
actually update the title/author fields after the form has already
mounted.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from ...state.book_detail_state import BookDetailState
from ...models.enums import BookGenre, BorrowingVisibility


def book_form(book_id="", submit_label: str = "Save") -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.input(name="book_id", value=book_id, type="hidden"),
            rx.hstack(
                rx.input(
                    placeholder="ISBN",
                    name="isbn",
                    value=BookDetailState.form_isbn,
                    on_change=BookDetailState.set_form_isbn,
                ),
                primary_button(
                    "☞ Look up", on_click=BookDetailState.fetch_isbn_metadata, type="button"
                ),
                spacing="2",
            ),
            rx.input(
                placeholder="Title",
                name="title",
                value=BookDetailState.form_title,
                on_change=BookDetailState.set_form_title,
                required=True,
            ),
            rx.input(
                placeholder="Author",
                name="author",
                value=BookDetailState.form_author,
                on_change=BookDetailState.set_form_author,
            ),
            rx.input(
                placeholder="Location (optional)",
                name="location",
                value=BookDetailState.form_location,
                on_change=BookDetailState.set_form_location,
            ),
            rx.select(
                ["—"] + [g.value for g in BookGenre],
                placeholder="Genre (optional)",
                name="genre",
                value=BookDetailState.form_genre,
                on_change=BookDetailState.set_form_genre,
            ),
            rx.select(
                [v.value for v in BorrowingVisibility],
                placeholder="Borrowing visibility",
                name="borrowing_visibility",
                value=BookDetailState.form_borrowing_visibility,
                on_change=BookDetailState.set_form_borrowing_visibility,
            ),
            primary_button(submit_label, type="submit"),
            spacing="3",
        ),
        on_submit=BookDetailState.submit_book_form,
    )


__all__ = ["book_form"]