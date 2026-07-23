"""Book detail page — minimal version, shows what we store ourselves
(title, author, ISBN, location as plain text, owner, loan history).

Deliberately lean: once title/ISBN search-and-fetch from Open Library
lands, the "add/enrich a book" flow changes shape substantially, and
this page will very likely be reworked alongside it. Not worth
polishing further right now.
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.library_state import LibraryState, LoanHistoryEntry


def _loan_history_row(entry: LoanHistoryEntry) -> rx.Component:
    return card(
        body_text(entry.borrower_name),
        meta_text(f"Loaned {entry.loan_date}, due {entry.due_date}"),
        rx.cond(
            entry.is_active,
            meta_text("Currently on loan"),
            meta_text(f"Returned {entry.return_date}"),
        ),
        margin_bottom="0.5rem",
    )


def book_detail() -> rx.Component:
    return shell(
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
            LibraryState.detail_book,
            rx.fragment(
                page_title(LibraryState.detail_book.title),
                rx.cond(
                    LibraryState.detail_book.author,
                    body_text(LibraryState.detail_book.author),
                ),
                meta_text(f"Owned by {LibraryState.detail_book.owner_name}"),
                meta_text(LibraryState.detail_book.status),
                rx.link(
                    "☞ Reviews",
                    href=f"/book/{LibraryState.detail_book.id}/reviews",
                    display="block",
                ),
                rx.link(
                    "☞ Synopsis",
                    href=f"/book/{LibraryState.detail_book.id}/synopsis",
                    display="block",
                ),
                rx.link(
                    "☞ Discussion",
                    href=f"/book/{LibraryState.detail_book.id}/discussion",
                    display="block",
                ),
                rx.cond(
                    LibraryState.detail_book.is_own_book,
                    rx.link(
                        "☞ Edit",
                        href=f"/book/{LibraryState.detail_book.id}/edit",
                        display="block",
                    ),
                ),
                rx.cond(
                    LibraryState.detail_book.isbn,
                    meta_text(f"ISBN: {LibraryState.detail_book.isbn}"),
                ),
                rx.cond(
                    LibraryState.detail_book.location,
                    meta_text(f"Location: {LibraryState.detail_book.location}"),
                ),
                divider(),
                page_title("Loan history"),
                rx.foreach(LibraryState.loan_history, _loan_history_row),
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["book_detail"]