"""Verify Email Pending — the sole destination for an unverified,
logged-in user, per the central Access Gate (AuthState.check_auth).
No navigation to the rest of the app is shown here — this page IS
the entire experience until the user confirms their email.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import shell
from ...state.auth_state import AuthState
from ...state.verify_email_pending_state import VerifyEmailPendingState


def verify_email_pending() -> rx.Component:
    return shell(
        page_title("Almost there!"),
        body_text(
            "We've sent a confirmation link to your email address. "
            "Please click it to unlock the rest of The Diodati Debtors."
        ),
        rx.cond(
            VerifyEmailPendingState.info_message != "",
            meta_text(VerifyEmailPendingState.info_message),
        ),
        rx.cond(
            VerifyEmailPendingState.error_message != "",
            meta_text(VerifyEmailPendingState.error_message),
        ),
        primary_button(
            "Resend confirmation email",
            on_click=VerifyEmailPendingState.resend,
            type="button",
        ),
        rx.link(
            "☞ Log out",
            href="/",
            on_click=AuthState.logout,
            margin_top="1rem",
            display="block",
        ),
        max_width="32rem",
    )


__all__ = ["verify_email_pending"]