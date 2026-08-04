"""Verify Email — the destination of the link sent by
auth_service._create_and_send_verification_token.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import body_text, page_title
from ..components.shell import shell
from ...state.verify_email_state import VerifyEmailState


def verify_email() -> rx.Component:
    return shell(
        page_title("Email Verification"),
        rx.cond(
            VerifyEmailState.success,
            body_text("Your email has been confirmed. You can now use all features."),
            rx.cond(
                VerifyEmailState.error_message != "",
                body_text(VerifyEmailState.error_message),
                body_text("Verifying..."),
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="32rem",
    )


__all__ = ["verify_email"]