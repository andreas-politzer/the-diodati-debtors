"""My Lent-Out History — grouped by book, not one row per loan. If
"Frankenstein" has been lent out five times, it appears once, with
all five lending periods listed underneath (Andy's request: avoid
the same book appearing repeatedly).
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import shell
from ...state.loan_activity_state import LentOutHistoryGroup, LentOutPeriod, LoanActivityState


def _period_row(period: LentOutPeriod) -> rx.Component:
    return rx.hstack(
        meta_text(f"Lent to {period.borrower_name}"),
        meta_text(
            rx.cond(
                period.return_date != None,
                f"{period.loan_date} – {period.return_date}",
                f"{period.loan_date} – present (still out)",
            )
        ),
        spacing="3",
        margin_bottom="0.25rem",
    )


def _book_group_card(group: LentOutHistoryGroup) -> rx.Component:
    return card(
        rx.link(page_title(group.book_title), href=f"/book/{group.book_id}"),
        rx.foreach(group.periods, _period_row),
        margin_bottom="1rem",
    )


def lent_out_books() -> rx.Component:
    return shell(
        page_title("My Lent-Out History"),
        rx.cond(
            LoanActivityState.lent_out_history.length() > 0,
            rx.foreach(LoanActivityState.lent_out_history, _book_group_card),
            body_text("You haven't lent out any books yet."),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["lent_out_books"]