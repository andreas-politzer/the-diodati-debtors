"""Community Guidelines — shown as a collapsible element directly
above post-composer forms (not buried in a footer link), so it's
visible right where it matters without forcing anyone to read it.
Same <details>/<summary> pattern already used for club descriptions.
"""

from __future__ import annotations

import reflex as rx

from .label import body_text


def community_guidelines() -> rx.Component:
    return rx.el.details(
        rx.el.summary("☞ Community Guidelines", cursor="pointer"),
        body_text(

    "Welcome to The Diodati Debtors. Be respectful, keep discussions "

    "centered on books, mark spoilers whenever possible, and treat "

    "borrowed books—and fellow readers—with care. Different tastes "

    "make better conversations. This is a quiet place for readers, "

    "where books always come first.",
            margin_top="0.5rem",
        ),
        margin_bottom="1rem",
    )


__all__ = ["community_guidelines"]