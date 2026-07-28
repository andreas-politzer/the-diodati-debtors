"""Synopsis page — own route (same pattern as Reviews, avoids the
book detail page becoming a scroll monster). Three ways to set a
summary: manual, Open Library fetch, AI-generated — owner-only, per
the Synopsis Pipeline concept (project vault).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button, warning_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.book_detail_state import BookDetailState


def synopsis() -> rx.Component:
    return shell(
        page_title("Synopsis"),
        rx.cond(
            BookDetailState.error_message != "",
            rx.text(
                BookDetailState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            BookDetailState.info_message != "",
            meta_text(BookDetailState.info_message),
        ),
        rx.cond(
            BookDetailState.detail_book,
            rx.fragment(
                rx.cond(
                    BookDetailState.detail_book.summary,
                    rx.fragment(
                        body_text(BookDetailState.detail_book.summary),
                        meta_text(f"Source: {BookDetailState.detail_book.summary_source}"),
                    ),
                    body_text("No summary yet."),
                ),
                rx.cond(
                    BookDetailState.detail_book.is_own_book,
                    rx.fragment(
                        divider(),
                        meta_text("Only the book's owner can set a summary."),
                        rx.form(
                            rx.vstack(
                                rx.text_area(
                                    placeholder="Write your own summary...",
                                    name="summary",
                                    value=BookDetailState.form_summary,
                                    on_change=BookDetailState.set_form_summary,
                                    rows="6",
                                ),
                                primary_button("Save my own summary", type="submit"),
                                spacing="3",
                            ),
                            on_submit=BookDetailState.submit_summary_manual,
                        ),
                        rx.hstack(
                            primary_button(
                                "Fetch from Open Library",
                                on_click=BookDetailState.fetch_summary_open_library,
                                type="button",
                            ),
                            primary_button(
                                "Generate with AI",
                                on_click=BookDetailState.generate_summary_ai,
                                type="button",
                            ),
                            rx.cond(
                                BookDetailState.pending_clear_summary,
                                rx.hstack(
                                    meta_text("Really clear the summary?"),
                                    warning_button(
                                        "Yes, clear it", on_click=BookDetailState.clear_summary
                                    ),
                                    primary_button(
                                        "Cancel", on_click=BookDetailState.cancel_clear_summary
                                    ),
                                    spacing="2",
                                ),
                                primary_button(
                                    "Clear summary",
                                    on_click=BookDetailState.confirm_clear_summary,
                                    type="button",
                                ),
                            ),
                            spacing="3",
                            margin_top="1rem",
                        ),
                    ),
                ),
            ),
        ),
        rx.link(
            "☞ Back to book", href=f"/book/{BookDetailState.book_id}", margin_top="1rem", display="block"
        ),
        max_width="40rem",
    )


__all__ = ["synopsis"]