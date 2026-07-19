"""Style-system preview page.

NOT a feature page. This exists solely so Phase 1 can be verified in a
real browser per the Release Gate ("a local browser check"), without
pulling in any book/loan/auth logic. Wire it to a throwaway route
temporarily, check it renders as expected, then leave it unrouted or
delete it once Phase 1 is signed off — it is not part of the permanent
page set described in Struktur.md (login/dashboard/book_detail/feed).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button, warning_button
from ..components.card import card
from ..components.label import body_text, display_numeral, meta_text, page_title
from ..components.shell import divider, shell


def style_preview() -> rx.Component:
    return shell(
        page_title("The Diodati Debtors"),
        meta_text("Design system preview — Phase 1, not a real page"),
        divider(),
        card(
            page_title("Trust Score"),
            display_numeral("VIII / X"),
            meta_text("Pure typography, no gauges or stars"),
        ),
        divider(),
        card(
            page_title("A Card"),
            body_text(
                "This is body text in Libre Baskerville, generously "
                "leaded for reading — the way a feed post or book "
                "description will look."
            ),
            meta_text("Posted 2 hours ago"),
        ),
        divider(),
        rx.hstack(
            primary_button("Lend Book"),
            warning_button("Mark Overdue"),
            spacing="3",
        ),
    )


__all__ = ["style_preview"]
