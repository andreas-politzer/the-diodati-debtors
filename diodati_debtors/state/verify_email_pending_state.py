"""Verify Email Pending state — the page an unverified user is
redirected to for every protected page, until they confirm their
email. Offers only a resend action, per the 04.08. central-gate
architecture decision (project vault).
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import auth_service
from .auth_state import AuthState


class VerifyEmailPendingState(rx.State):
    info_message: str = ""
    error_message: str = ""

    async def resend(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return

        try:
            auth_service.resend_verification_email(int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.info_message = "A new verification email has been sent."


__all__ = ["VerifyEmailPendingState"]