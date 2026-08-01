"""Member detail page — profile (if visible) plus a read-only view of
one member's personal library. Trust signals get their own compact
card, separate from self-authored profile fields.
"""

from __future__ import annotations

import reflex as rx

from ..components.book_row import book_row
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.member_library_state import MemberLibraryState


def member_detail() -> rx.Component:
    return shell(
        page_title(MemberLibraryState.viewing_member_name),
        rx.cond(
            MemberLibraryState.viewing_member_shows_library,
            card(
                meta_text(f"Reliability: {MemberLibraryState.viewing_member_reliability}"),
                meta_text(f"Book Care: {MemberLibraryState.viewing_member_book_care}"),
                width="fit-content",
            ),
        ),
        rx.hstack(
            page_title("Profile", font_size="1.3rem"),
            meta_text(f"({MemberLibraryState.viewing_member_visibility_label})"),
            spacing="2",
            align="center",
        ),
        rx.cond(
            MemberLibraryState.viewing_member_profile_visible,
            card(
                rx.cond(
                    MemberLibraryState.viewing_member_location != "",
                    meta_text(f"Location: {MemberLibraryState.viewing_member_location}"),
                ),
                rx.cond(
                    MemberLibraryState.viewing_member_favorite_genre != "",
                    meta_text(f"Favourite genre: {MemberLibraryState.viewing_member_favorite_genre}"),
                ),
                rx.cond(
                    MemberLibraryState.viewing_member_bio != "",
                    body_text(MemberLibraryState.viewing_member_bio, margin_top="0.5rem"),
                ),
                width="fit-content",
                max_width="24rem",
            ),
            card(meta_text("This member's profile is private."), width="fit-content"),
        ),
        rx.cond(
            MemberLibraryState.viewing_member_shows_library,
            rx.fragment(
                divider(),
                page_title("Personal Library", font_size="1.3rem"),
                rx.grid(
                    rx.foreach(MemberLibraryState.member_books, book_row),
                    columns="repeat(auto-fill, minmax(220px, 1fr))",
                    gap="1rem",
                    width="100%",
                ),
            ),
        ),
        rx.link("☞ Back to members", href="/members", margin_top="1rem", display="block"),
        max_width="80rem",
    )


__all__ = ["member_detail"]