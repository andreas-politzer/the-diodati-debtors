"""Landing page — public, no login required."""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import body_text, page_title
from ..components.shell import shell


def landing() -> rx.Component:
    return shell(
        page_title("The Diodati Debtors"),
        body_text(
            "A small library for a small circle of readers. Catalogue "
            "your own books, lend and borrow within the group, and see "
            "who still owes whom a return."
        ),
        rx.link(primary_button("Log in"), href="/login"),
        rx.link("☞ Register instead", href="/register", margin_top="1rem", display="block"),
        max_width="36rem",
    )


__all__ = ["landing"]