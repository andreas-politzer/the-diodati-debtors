"""Manual — a short, practical walkthrough for new users. Same
pattern as Imprint/Privacy: a simple, static page, linked from the
shell footer.
"""

from __future__ import annotations

import reflex as rx

from ..components.label import body_text, page_title
from ..components.shell import divider, shell


def manual() -> rx.Component:
    return shell(
        page_title("Manual"),
        body_text(
            "A quick walkthrough of how The Diodati Debtors works."
        ),
        divider(),
        page_title("Getting started", font_size="1.3rem"),
        body_text("1. Register an account and log in."),
        body_text(
            "2. Your Personal Library works right away, with no club "
            "required — add your own books via ISBN lookup, title "
            "search, or manually."
        ),
        body_text(
            "3. Found a club, or browse existing clubs and request to "
            "join one. A club gives you a Common Club Library — every "
            "book owned by any member of that club."
        ),
        divider(),
        page_title("Lending and borrowing", font_size="1.3rem"),
        body_text(
            "To borrow a club member's book, click \"Request to "
            "borrow\" — you can propose a custom loan period and leave "
            "a note. The owner approves or declines, optionally with a "
            "reply message."
        ),
        body_text(
            "When you get a book back, click \"Mark returned\" — you "
            "can optionally rate its condition."
        ),
        body_text(
            "Lending to someone without an account (a neighbour, a "
            "family member)? Add them as a Contact and lend directly — "
            "no request needed, since they never use the app."
        ),
        divider(),
        page_title("Trust signals", font_size="1.3rem"),
        body_text(
            "Reliability and Book Care are shown for members and "
            "contacts you might lend to — always as plain words "
            "(Excellent, Good, ...), never as scores or rankings."
        ),
        divider(),
        page_title("Organize", font_size="1.3rem"),
        body_text(
            "Pending join requests and loan requests that need your "
            "decision live here, along with the status of requests "
            "you've sent yourself."
        ),
        divider(),
        page_title("Community", font_size="1.3rem"),
        body_text(
            "Club Feed and Global Board are for posts and discussion. "
            "Every book also has its own Discussion, Reviews, and "
            "Synopsis (written manually, imported from Open Library, "
            "or AI-generated)."
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["manual"]