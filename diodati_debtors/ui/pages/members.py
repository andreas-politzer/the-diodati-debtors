"""Members page — every member of every club the current user belongs
to, grouped by club. Answers "who's in which of MY clubs", not just
the currently-selected one.
"""

from __future__ import annotations

import reflex as rx

from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.group_state import ClubMembersView, MemberEntry, GroupState


def _member_link(member: MemberEntry) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.text("☞", font_size="1.5rem", line_height="1"),
            body_text(member.display_name),
            meta_text(member.role),
            spacing="2",
            align="center",
        ),
        href=f"/members/{member.user_id}",
        display="block",
        margin_bottom="0.5rem",
    )


def _club_section(club: ClubMembersView) -> rx.Component:
    return card(
        page_title(club.group_name),
        rx.foreach(club.members, _member_link),
        margin_bottom="1rem",
    )


def members() -> rx.Component:
    return shell(
        page_title("Members"),
        rx.cond(
            GroupState.has_groups,
            rx.foreach(GroupState.club_members, _club_section),
            rx.fragment(
                body_text("You're not a member of any club yet."),
                rx.link("☞ Go to your clubs", href="/clubs", margin_top="0.5rem", display="block"),
            ),
        ),
        divider(),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["members"]