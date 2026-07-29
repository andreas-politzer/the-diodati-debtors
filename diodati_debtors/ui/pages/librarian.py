"""Ask the Librarian — semantic book recommendation, named after Lord
Byron ("Georgie"), who was actually present at Villa Diodati in 1816
(see Ask the Librarian Vision, project vault). Wider two-column
layout — this is the project's flagship feature, not another 40rem
page.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.librarian_state import ExternalBookView, LibrarianState, MatchView


def _match_card(match: MatchView) -> rx.Component:
    return card(
        rx.link(page_title(match.title), href=f"/book/{match.book_id}"),
        rx.cond(match.author, body_text(match.author)),
        margin_bottom="1rem",
    )


def _external_book_card(book: ExternalBookView) -> rx.Component:
    return card(
        rx.cond(
            book.cover_url != "",
            rx.image(src=book.cover_url, width="100px", margin_bottom="0.5rem"),
        ),
        page_title(book.title),
        rx.cond(book.author != "", body_text(book.author)),
        margin_bottom="1rem",
    )


def librarian() -> rx.Component:
    return shell(
        page_title("Ask the Librarian"),
        rx.hstack(
            rx.image(
                src="/images/lord-byron-sepia.png",
                width="280px",
                border_radius="4px",
            ),
            rx.vstack(
                body_text(
                    "Tell the librarian what you're looking for — a mood, "
                    "a theme, a half-remembered detail."
                ),
                rx.text_area(
                    placeholder="e.g. Sweden, and maybe a big dog...",
                    value=LibrarianState.query,
                    on_change=LibrarianState.set_query,
                    rows="3",
                    width="100%",
                ),
                primary_button("Ask", on_click=LibrarianState.ask, type="button"),
                body_text(
                    "Pray, afford Master Georgie a moment's patience – the poor "
                    "fellow was born in 1788, and though still in the prime of "
                    "manhood, one must allow that the years begin to weigh upon "
                    "a gentleman of such advanced standing."
                ),
                rx.cond(
                    LibrarianState.error_message != "",
                    rx.text(
                        LibrarianState.error_message,
                        font_family=Font.system,
                        font_size=Type.meta,
                        color=Color.warning,
                    ),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            
            spacing="5",
            align="start",
            width="100%",
        ),
        rx.cond(
            LibrarianState.has_searched,
            rx.fragment(
                divider(),
                rx.cond(
                        LibrarianState.matches.length() > 0,
                        rx.fragment(
                            rx.cond(LibrarianState.external_remark != "", body_text(LibrarianState.external_remark)),
                            rx.foreach(LibrarianState.matches, _match_card),
                        ),
                    rx.fragment(
                        rx.cond(
                            LibrarianState.restricted_club_name != "",
                            body_text(
                                f"The librarian knows of a match, but it belongs to a "
                                f"club you haven't joined yet: "
                                f"{LibrarianState.restricted_club_name}. Ask to join, "
                                f"and you may find your answer there."
                            ),
                        ),
                        rx.cond(
                            LibrarianState.external_remark != "",
                            rx.vstack(
                                body_text(LibrarianState.external_remark),
                                rx.foreach(LibrarianState.external_books, _external_book_card),
                                rx.cond(
                                    LibrarianState.external_books.length() > 0,
                                    rx.vstack(
                                        meta_text("Continue your search"),
                                        rx.text(
                                            LibrarianState.external_books_copy_text,
                                            white_space="pre-wrap",
                                            font_family=Font.system,
                                            font_size=Type.meta,
                                        ),
                                        primary_button(
                                            "Copy all",
                                            on_click=rx.set_clipboard(LibrarianState.external_books_copy_text),
                                            type="button",
                                        ),
                                        spacing="2",
                                        margin_top="1rem",
                                        padding="0.75rem",
                                        border=f"1px solid {Color.text_soft}",
                                        border_radius="4px",
                                    ),
                                ),
                                spacing="3",
                                margin_top="1rem",
                            ),
                        ),
                    ),
                ),
            ),
        ),
        divider(),
        meta_text("Our Librarian, Georgie — Lord Byron, early 19th-century portrait engraving (public domain), colorized."),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="64rem",
    )


__all__ = ["librarian"]