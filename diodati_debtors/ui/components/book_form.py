"""Shared Add/Edit Book form. One component, one handler
(LibraryState.submit_book_form) — no duplicated Add/Edit forms, per
Codex's review. Presence of a non-empty book_id (hidden field)
distinguishes edit from create; the state handler branches on it.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from ...state.library_state import LibraryState


def book_form(
    book_id=0,
    initial_title="",
    initial_author="",
    initial_isbn="",
    initial_location="",
    submit_label: str = "Save",
) -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.input(name="book_id", value=book_id, type="hidden"),
            rx.input(
                placeholder="Title",
                name="title",
                default_value=initial_title,
                required=True,
            ),
            rx.input(placeholder="Author", name="author", default_value=initial_author),
            rx.input(placeholder="ISBN", name="isbn", default_value=initial_isbn),
            rx.input(
                placeholder="Location (optional)",
                name="location",
                default_value=initial_location,
            ),
            primary_button(submit_label, type="submit"),
            spacing="3",
        ),
        on_submit=LibraryState.submit_book_form,
        reset_on_submit=(book_id == 0),
    )


__all__ = ["book_form"]