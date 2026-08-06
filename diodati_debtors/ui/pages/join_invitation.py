"""Join Invitation — the destination of a Club Invitation link.
Distinguishes three states: not logged in, logged in with the correct
account, logged in with a different account (per the 05.08.
architecture decision, project vault — never auto-accept for a
mismatched account).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button, warning_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import shell
from ...state.auth_state import AuthState
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
                rx.cond(
                    JoinInvitationState.wrong_account,
                    rx.vstack(
                        body_text(
                            f"This invitation was sent to {JoinInvitationState.invited_email}."
                        ),
                        meta_text(
                            f"You are currently signed in as {JoinInvitationState.current_account_email}."
                        ),
                        warning_button(
                            "Sign out and continue",
                            on_click=JoinInvitationState.sign_out_and_continue,
                            type="button",
                        ),
                        spacing="3",
                    ),
                    rx.cond(
                        AuthState.is_logged_in,
                        rx.vstack(
                            body_text(f"You've been invited to join {JoinInvitationState.group_name}."),
                            primary_button(
                                "Accept Invitation", on_click=JoinInvitationState.accept, type="button"
                            ),
                            spacing="3",
                        ),
                        rx.vstack(
                            body_text(f"You've been invited to join {JoinInvitationState.group_name}."),
                            body_text(f"Create an account with {JoinInvitationState.invited_email} to accept."),
                            rx.link(
                                primary_button("Create Account", type="button"),
                                href=f"/register?invitation={JoinInvitationState.token}",
                            ),
                            rx.link(
                                "☞ Already have an account? Log in",
                                href="/login",
                                margin_top="0.5rem",
                                display="block",
                            ),
                            spacing="3",
                        ),
                    ),
                ),
            ),
        ),
        rx.cond(
            AuthState.is_logged_in,
            rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        ),
        max_width="32rem",
    )


__all__ = ["join_invitation"]