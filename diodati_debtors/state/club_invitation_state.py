"""Club Invitation state — the adapter between Reflex UI and
club_invitation_service, integrated into My Bookmates (per the 04.08.
UX decision, project vault): invitations are relationships between
people, not a separate technical feature.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import club_invitation_service, group_service
from .auth_state import AuthState


@dataclass
class PendingInvitationView:
    id: int
    group_name: str
    invited_email: str
    created_at: str


@dataclass
class InvitableGroupOption:
    id: str
    name: str


class ClubInvitationState(rx.State):
    pending_invitations: list[PendingInvitationView] = []
    invitable_groups: list[InvitableGroupOption] = []
    invite_email_draft: str = ""
    invite_group_id_draft: str = ""
    error_message: str = ""
    info_message: str = ""

    def set_invite_email_draft(self, value: str):
        self.invite_email_draft = value

    def set_invite_group_id_draft(self, value: str):
        self.invite_group_id_draft = value

    async def load_invitations(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.pending_invitations = []
            self.invitable_groups = []
            return

        user_id = int(auth_state.current_user_id)

        try:
            groups = group_service.list_groups_for_user(user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.invitable_groups = [
            InvitableGroupOption(id=str(g.id), name=g.name) for g in groups
        ]

        views: list[PendingInvitationView] = []
        for group in groups:
            try:
                invitations = club_invitation_service.list_pending_invitations_for_group(group.id)
            except DiodatiError:
                continue
            for inv in invitations:
                views.append(
                    PendingInvitationView(
                        id=inv.id,
                        group_name=group.name,
                        invited_email=inv.invited_email,
                        created_at=inv.created_at.isoformat() if hasattr(inv.created_at, "isoformat") else str(inv.created_at),
                    )
                )
        self.pending_invitations = views

    @rx.var
    def invitable_group_names(self) -> list[str]:
        return [g.name for g in self.invitable_groups]

    def set_invite_group_name_draft(self, value: str):
        self.invite_group_id_draft = next(
            (g.id for g in self.invitable_groups if g.name == value), ""
        )

    async def send_invitation(self):
        self.error_message = ""
        self.info_message = ""

        if not self.invite_email_draft.strip():
            self.error_message = "Enter an email address."
            return
        if not self.invite_group_id_draft:
            self.error_message = "Choose a club."
            return

        auth_state = await self.get_state(AuthState)
        try:
            club_invitation_service.invite_to_club(
                int(self.invite_group_id_draft),
                int(auth_state.current_user_id),
                self.invite_email_draft,
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.invite_email_draft = ""
        self.info_message = "Invitation sent."
        await self.load_invitations()


__all__ = ["ClubInvitationState", "PendingInvitationView", "InvitableGroupOption"]