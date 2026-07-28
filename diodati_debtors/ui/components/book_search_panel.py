"""Title search panel — a separate way to populate BookForm, distinct
from ISBN lookup. Presents candidate matches (with cover art from
Open Library's Covers API) for the user to choose from; never
auto-selects. Reuses the same BookDetailState.form_* fields — BookForm
never needs to know where the data came from.

Cover images use the flat, restrained treatment from the Phase 1
Design Contract: grayscale 20% + sepia 10%, removed on hover.
"""

from __future__ import annotations

import reflex as rx

from .button import primary_button
from .label import meta_text
from ...state.book_detail_state import BookDetailState, BookSearchResultView


def _result_card(result: BookSearchResultView) -> rx.Component:
    return rx.hstack(
        rx.cond(
            result.cover_url,
            rx.image(
                src=result.cover_url,
                width="60px",
                height="90px",
                object_fit="cover",
                filter="grayscale(20%) sepia(10%)",
                _hover={"filter": "none"},
            ),
        ),
        rx.vstack(
            rx.text(result.title, font_weight="700"),
            rx.cond(result.author, meta_text(result.author)),
            rx.cond(
                result.publish_year,
                meta_text(f"First published {result.publish_year}"),
            ),
            primary_button(
                "Use this",
                on_click=lambda: BookDetailState.select_search_result(result.work_key),
                type="button",
            ),
            spacing="1",
            align="start",
        ),
        spacing="3",
        margin_bottom="1rem",
        align="start",
    )


def book_search_panel() -> rx.Component:
    return rx.vstack(
        meta_text("Search Open Library by title or author"),
        rx.hstack(
            rx.input(
                placeholder="",
                value=BookDetailState.search_query,
                on_change=BookDetailState.set_search_query,
            ),
            primary_button("☞ Search", on_click=BookDetailState.run_search, type="button"),
            spacing="2",
        ),
        rx.cond(
            BookDetailState.search_results.length() > 0,
            rx.vstack(
                rx.foreach(BookDetailState.search_results, _result_card),
                primary_button(
                    "Clear results", on_click=BookDetailState.clear_search, type="button"
                ),
                spacing="2",
                margin_top="1rem",
            ),
        ),
        spacing="2",
        margin_bottom="1.5rem",
    )


__all__ = ["book_search_panel"]