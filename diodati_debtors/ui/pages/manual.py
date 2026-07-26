"""Manual — walks through the app in the exact order the user
encounters it on the Dashboard: nav links first, then the four
Personal/Common/Borrowed/Lent-Out tabs. Images float within the text,
part of the flow rather than separate academic figures.
"""

from __future__ import annotations

import reflex as rx

from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell


def manual() -> rx.Component:
    return shell(
        page_title("Manual"),
        rx.image(
            src="/images/manual-bible.jpg",
            width="600px",
            float="left",
            margin_right="1.5rem",
            margin_bottom="0.5rem",
        ),
        body_text(
            "A walkthrough of The Diodati Debtors, in the order you'll "
            "actually encounter things — starting with the links on "
            "your Dashboard, then the four tabs that hold your books "
            "and loans."
        ),
        body_text(
            "Register an account and log in — your Personal Library "
            "works right away, with no club required."
        ),
        rx.box(clear="both"),
        divider(),
        page_title("Add a Book", font_size="1.3rem"),
        body_text(
            "Add a book via ISBN lookup, title search (with cover "
            "previews), or entirely by hand."
        ),
        divider(),
        page_title("Clubs", font_size="1.3rem"),
        body_text(
            "Found a club, or browse and request to join an existing "
            "one. A club gives every member a shared Common Club "
            "Library — every book owned by any of its members."
        ),
        divider(),
        page_title("My Bookmates", font_size="1.3rem"),
        rx.image(
            src="/images/manual.jpg",
            width="480px",
            float="right",
            margin_left="1.5rem",
            margin_bottom="0.5rem",
        ),
        body_text(
            "Club Members and personal Contacts, side by side. Contacts "
            "are people without an account — a neighbour, a family "
            "member — who you lend to and manage directly, with no "
            "request needed."
        ),
        divider(),
        page_title("Organize", font_size="1.3rem"),
        body_text(
            "\"What needs my attention?\" — pending club-join and "
            "loan requests to decide on, plus Your Requests: what "
            "you've sent, and the status of each."
        ),
        divider(),
        page_title("Communication", font_size="1.3rem"),
        body_text(
            "Club Feed and Global Board for posts and discussion. "
            "Every book also has its own Discussion, Reviews, and "
            "Synopsis (written manually, imported from Open Library, "
            "or AI-generated)."
        ),
        divider(),
        page_title("Ask the Librarian", font_size="1.3rem"),
        body_text(
            "Describe what you're looking for in your own words — a "
            "mood, a theme, a half-remembered detail. The librarian "
            "searches your library's meaning, not just its words, and "
            "will suggest something from beyond it if nothing fits."
        ),
        divider(),
        page_title("The Dashboard Tabs", font_size="1.3rem"),
        body_text(
            "Personal Library — your own books, always visible, no "
            "club required."
        ),
        body_text(
            "Common Club Library — every book owned by any member of "
            "your currently selected club (switch clubs from the "
            "dropdown above the tabs)."
        ),
        body_text(
            "My Borrowed Books — what you currently have on loan, plus "
            "a link to your full Borrow History."
        ),
        body_text(
            "My Lent-Out Books — books you own that are currently out "
            "with someone else, plus a link to your Lent-Out History, "
            "grouped by book."
        ),
        divider(),
        page_title("Trust Signals", font_size="1.3rem"),
        body_text(
            "Reliability and Book Care are shown wherever they help you "
            "decide who to lend to — always as plain words (Excellent, "
            "Good, ...), never as scores or rankings."
        ),
        divider(),
        meta_text(
            "Illustrations from Manual of the System of the British and "
            "Foreign School Society of London, London, 1816 — the same "
            "year as Villa Diodati."
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="64rem",
    )


__all__ = ["manual"]