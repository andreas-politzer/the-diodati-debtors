"""Join Invitation state — handles the /join-invitation/[token] link.
Distinguishes three states (per the 05.08. architecture decision,
project vault): not logged in (offer registration with the invited
email pre-filled), logged in with the correct email (accept
directly), logged in with a different email (explicit mismatch,
never auto-accept).
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import club_invitation_service, user_service
from .auth_state import AuthState


class JoinInvitationState(rx.State):
    group_name: str = ""
    invited_email: str = ""
    success: bool = False
    error_message: str = ""
    wrong_account: bool = False
    current_account_email: str = ""

    async def load_invitation(self):
        self.error_message = ""
        self.wrong_account = False
        try:
            invitation = club_invitation_service.get_invitation(self.token)
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.group_name = invitation.group_name
        self.invited_email = invitation.invited_email

        auth_state = await self.get_state(AuthState)
        if auth_state.is_logged_in:
            try:
                current_user = user_service.get_user(int(auth_state.current_user_id))
            except DiodatiError:
                return
            self.current_account_email = current_user.email
            if current_user.email.lower() != invitation.invited_email.lower():
                self.wrong_account = True

    async def accept(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "Please log in or register first."
            return

        try:
            club_invitation_service.accept_invitation(self.token, int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.success = True

    def sign_out_and_continue(self):
        return [AuthState.logout, rx.redirect(f"/join-invitation/{self.token}")]


__all__ = ["JoinInvitationState"]