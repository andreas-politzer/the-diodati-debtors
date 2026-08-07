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
            "Register an account, then confirm your email address via "
            "the link we send you — after that, your Personal Library "
            "works right away, with no club required."
        ),
        rx.box(clear="both"),
        divider(),
        page_title("Add a Book", font_size="1.3rem"),
        body_text(
            "Add a book via ISBN lookup, title search (with cover "
            "previews), or entirely by hand. Set its Borrowing "
            "Visibility to control whether it's only visible within "
            "your club, or open to public borrowing enquiries from "
            "anyone on the platform."
        ),
        divider(),
        page_title("Import Books", font_size="1.3rem"),
        body_text(
            "Already have a spreadsheet of your books? Upload a CSV, "
            "XLSX, or ODS file — the columns are detected for you, "
            "likely duplicates are flagged for review, and you'll see "
            "exactly what was added or skipped once it's done."
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
        body_text(
            "Invite a friend by email — they'll get a link straight "
            "into your club, with their account already confirmed, no "
            "separate verification step needed."
        ),
        divider(),
        page_title("My Profile", font_size="1.3rem"),
        body_text(
            "Entirely optional: a display name, location, bio, and "
            "favourite genre, with one visibility setting for the "
            "whole thing — private, visible to fellow club members, or "
            "public."
        ),
        divider(),
        page_title("Organise", font_size="1.3rem"),
        body_text(
            "\"What needs my attention?\" — pending club-join and "
            "loan requests to decide on, open Borrowing Inquiries "
            "waiting on your reply, plus Your Requests: what you've "
            "sent, and the status of each."
        ),
        divider(),
        page_title("Communication", font_size="1.3rem"),
        body_text(
            "A hub with three doors: Personal Messages (a WhatsApp-"
            "style overview of your ongoing conversations with fellow "
            "club members), Club Feed, and Global Board. Every book "
            "also has its own Discussion, Reviews, and Synopsis "
            "(written manually, imported from Open Library, or "
            "AI-generated)."
        ),
        divider(),
        page_title("Ask the Librarian", font_size="1.3rem"),
        body_text(
            "Describe what you're looking for in your own words — a "
            "mood, a theme, a half-remembered detail, or a specific "
            "title or author. The librarian checks your library's "
            "records first, then its meaning, and will suggest "
            "something from beyond it if nothing fits — verified "
            "against real sources before it's ever shown. If a match "
            "exists in a club you haven't joined, and its owner has "
            "opened it up to public enquiries, you can request to "
            "borrow it directly, no membership required."
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
            "Good, ...), never as scores or rankings. Only visible in "
            "contexts where they're actually relevant, such as a "
            "shared club."
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