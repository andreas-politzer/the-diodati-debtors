"""Join Invitation — the destination of a Club Invitation link. If
the user is logged in, they can accept directly; otherwise they're
pointed to log in/register first, then return to this same link.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import body_text, page_title
from ..components.shell import shell
from ...state.join_invitation_state import JoinInvitationState


def join_invitation() -> rx.Component:
    return shell(
        page_title("Club Invitation"),
        rx.cond(
            JoinInvitationState.success,
            body_text("Welcome! You've joined the club."),
            rx.cond(
                JoinInvitationState.error_message != "",
                body_text(JoinInvitationState.error_message),
                rx.vstack(
                    body_text(f"You've been invited to join {JoinInvitationState.group_name}."),
                    primary_button("Accept Invitation", on_click=JoinInvitationState.accept, type="button"),
                    spacing="3",
                ),
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="32rem",
    )


__all__ = ["join_invitation"]