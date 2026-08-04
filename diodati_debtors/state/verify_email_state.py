"""Verify Email state — handles the /verify-email/[token] link a user
clicks from their inbox.
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import auth_service


class VerifyEmailState(rx.State):
    success: bool = False
    error_message: str = ""

    async def verify(self):
        self.error_message = ""
        self.success = False

        try:
            auth_service.verify_email(self.token)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.success = True


__all__ = ["VerifyEmailState"]