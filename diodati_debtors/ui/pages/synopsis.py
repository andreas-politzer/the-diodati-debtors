"""Synopsis page — own route (same pattern as Reviews, avoids the
book detail page becoming a scroll monster). Three ways to set a
summary: manual, Open Library fetch, AI-generated — owner-only, per
the Synopsis Pipeline concept (project vault).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.button import warning_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.library_state import LibraryState


def synopsis() -> rx.Component:
    return shell(
        page_title("Synopsis"),
        rx.cond(
            LibraryState.error_message != "",
            rx.text(
                LibraryState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            LibraryState.info_message != "",
            meta_text(LibraryState.info_message),
        ),
        rx.cond(
            LibraryState.detail_book,
            rx.fragment(
                rx.cond(
                    LibraryState.detail_book.summary,
                    rx.fragment(
                        body_text(LibraryState.detail_book.summary),
                        meta_text(f"Source: {LibraryState.detail_book.summary_source}"),
                    ),
                    body_text("No summary yet."),
                ),
                rx.cond(
                    LibraryState.detail_book.is_own_book,
                    rx.fragment(
                        divider(),
                        meta_text("Only the book's owner can set a summary."),
                        rx.form(
                            rx.vstack(
                                rx.text_area(
                                    placeholder="Write your own summary...",
                                    name="summary",
                                    value=LibraryState.form_summary,
                                    on_change=LibraryState.set_form_summary,
                                    rows="6",
                                ),
                                primary_button("Save my own summary", type="submit"),
                                spacing="3",
                            ),
                            on_submit=LibraryState.submit_summary_manual,
                        ),
                        rx.hstack(
                            primary_button(
                                "Fetch from Open Library",
                                on_click=LibraryState.fetch_summary_open_library,
                                type="button",
                            ),
                            primary_button(
                                "Generate with AI",
                                on_click=LibraryState.generate_summary_ai,
                                type="button",
                            ),
                            rx.cond(
                                LibraryState.pending_clear_summary,
                                rx.hstack(
                                    meta_text("Really clear the summary?"),
                                    warning_button(
                                        "Yes, clear it", on_click=LibraryState.clear_summary
                                    ),
                                    primary_button(
                                        "Cancel", on_click=LibraryState.cancel_clear_summary
                                    ),
                                    spacing="2",
                                ),
                                primary_button(
                                    "Clear summary",
                                    on_click=LibraryState.confirm_clear_summary,
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
            "☞ Back to book", href=f"/book/{LibraryState.book_id}", margin_top="1rem", display="block"
        ),
        max_width="40rem",
    )


__all__ = ["synopsis"]