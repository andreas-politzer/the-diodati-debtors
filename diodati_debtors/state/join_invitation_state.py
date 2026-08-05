"""Join Invitation state — handles the /join-invitation/[token] link
a user clicks from their inbox. If not logged in, prompts them to
register/login first, then accepts the invitation automatically.
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import club_invitation_service
from .auth_state import AuthState


class JoinInvitationState(rx.State):
    group_name: str = ""
    success: bool = False
    error_message: str = ""

    async def load_invitation(self):
        self.error_message = ""
        try:
            invitation = club_invitation_service.get_invitation(self.token)
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.group_name = invitation.group_name

    async def accept(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "Please log in or register first, then return to this link."
            return

        try:
            invitation = club_invitation_service.get_invitation(self.token)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        from ..services import user_service
        try:
            current_user = user_service.get_user(int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return

        if current_user.email.lower() != invitation.invited_email.lower():
            self.error_message = (
                f"This invitation was sent to {invitation.invited_email}. "
                f"You are currently signed in as {current_user.email}. "
                f"Please sign out and log in with the invited email address."
            )
            return

        try:
            club_invitation_service.accept_invitation(self.token, int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.success = True

    


__all__ = ["JoinInvitationState"]