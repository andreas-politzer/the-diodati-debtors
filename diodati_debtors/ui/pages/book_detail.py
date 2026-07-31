"""Book detail page — minimal version, shows what we store ourselves
(title, author, ISBN, location as plain text, owner, loan history).
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.book_detail_state import BookDetailState, LoanHistoryEntry


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
            BookDetailState.error_message != "",
            rx.text(
                BookDetailState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            BookDetailState.detail_book,
            rx.fragment(
                page_title(BookDetailState.detail_book.title),
                rx.cond(
                    BookDetailState.detail_book.author,
                    body_text(BookDetailState.detail_book.author),
                ),
                meta_text(f"Owned by {BookDetailState.detail_book.owner_name}"),
                meta_text(BookDetailState.detail_book.status),
                meta_text(BookDetailState.detail_book.borrowing_visibility.replace("_", " ")),
                rx.link(
                    "☞ Reviews",
                    href=f"/book/{BookDetailState.detail_book.id}/reviews",
                    display="block",
                ),
                rx.link(
                    "☞ Synopsis",
                    href=f"/book/{BookDetailState.detail_book.id}/synopsis",
                    display="block",
                ),
                rx.link(
                    "☞ Discussion",
                    href=f"/book/{BookDetailState.detail_book.id}/discussion",
                    display="block",
                ),
                rx.cond(
                    BookDetailState.detail_book.is_own_book,
                    rx.link(
                        "☞ Edit",
                        href=f"/book/{BookDetailState.detail_book.id}/edit",
                        display="block",
                    ),
                ),
                rx.cond(
                    BookDetailState.detail_book.isbn,
                    meta_text(f"ISBN: {BookDetailState.detail_book.isbn}"),
                ),
                rx.cond(
                    BookDetailState.detail_book.location,
                    meta_text(f"Location: {BookDetailState.detail_book.location}"),
                ),
                divider(),
                page_title("Loan history"),
                rx.foreach(BookDetailState.loan_history, _loan_history_row),
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["book_detail"]