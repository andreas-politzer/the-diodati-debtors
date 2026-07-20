"""Shared Add/Edit Book form. One component, one handler
(LibraryState.submit_book_form). Fields are controlled (value= bound
to LibraryState.form_*) rather than default_value/uncontrolled — this
is what makes the ISBN lookup button able to actually update the
title/author fields after the form has already mounted.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from ...state.library_state import LibraryState


def book_form(book_id=0, submit_label: str = "Save") -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.input(name="book_id", value=book_id, type="hidden"),
            rx.hstack(
                rx.input(
                    placeholder="ISBN",
                    name="isbn",
                    value=LibraryState.form_isbn,
                    on_change=LibraryState.set_form_isbn,
                ),
                primary_button(
                    "☞ Look up", on_click=LibraryState.fetch_isbn_metadata, type="button"
                ),
                spacing="2",
            ),
            rx.input(
                placeholder="Title",
                name="title",
                value=LibraryState.form_title,
                on_change=LibraryState.set_form_title,
                required=True,
            ),
            rx.input(
                placeholder="Author",
                name="author",
                value=LibraryState.form_author,
                on_change=LibraryState.set_form_author,
            ),
            rx.input(
                placeholder="Location (optional)",
                name="location",
                value=LibraryState.form_location,
                on_change=LibraryState.set_form_location,
            ),
            primary_button(submit_label, type="submit"),
            spacing="3",
        ),
        on_submit=LibraryState.submit_book_form,
    )


__all__ = ["book_form"]