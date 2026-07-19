"""Landing page — public, no login required.

Deliberately minimal: title, one-line description, entry point into
the library. Expands later with real auth (register/login links)
rather than being thrown away.
"""

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
        rx.link(primary_button("Enter the library"), href="/dashboard"),
        max_width="36rem",
    )


__all__ = ["landing"]