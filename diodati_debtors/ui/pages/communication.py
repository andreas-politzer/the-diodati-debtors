"""Communication hub — links to the two book-independent Post
projections (Club Feed, Global Board). Book Discussion is
deliberately NOT here — it only makes sense attached to a specific
book, so it stays linked from the Book Detail page instead.
"""

from __future__ import annotations

import reflex as rx

from ..components.label import page_title
from ..components.shell import shell


def communication() -> rx.Component:
    return shell(
        page_title("Communication"),
        rx.link("☞ Club Feed", href="/club-feed", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Global Board", href="/board", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="32rem",
    )


__all__ = ["communication"]