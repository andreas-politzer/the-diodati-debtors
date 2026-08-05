"""Club Invitation service — the full domain concept of inviting
someone to join a club, independent of delivery channel (email via
Brevo today). Per the 04.08. architecture decision (project vault):
domain vs. adapter, same separation as Ask the Librarian uses for
Gemini/Google Books.
"""

from __future__ import annotations

import datetime as dt
import secrets

from dataclasses import dataclass

from sqlalchemy import select

from ..core.config import settings
from ..core.exceptions import (
    AlreadyGroupMemberError,
    DiodatiError,
    NotFoundError,
)
from ..core.normalize import normalize_email
from ..core.time import utcnow
from ..db.session import get_session
from ..models.club_invitation import ClubInvitation
from ..models.group import Group, GroupMembership
from ..models.user import User
from .external.email_client import send_email
from ..models.enums import GroupRole

_INVITATION_VALID_DAYS = 7


class InvitationNotAllowedError(DiodatiError):
    """Raised when the inviter is not a member of the group, or the
    invited email already belongs to a current member."""


@dataclass(frozen=True)
class ClubInvitationResult:
    id: int
    group_id: int
    group_name: str
    inviter_id: int
    invited_email: str
    token: str
    accepted_at: dt.datetime | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "group_name": self.group_name,
            "inviter_id": self.inviter_id,
            "invited_email": self.invited_email,
            "token": self.token,
            "accepted_at": self.accepted_at,
        }


def _to_result(invitation: ClubInvitation) -> ClubInvitationResult:
    return ClubInvitationResult(
        id=invitation.id,
        group_id=invitation.group_id,
        group_name=invitation.group.name,
        inviter_id=invitation.inviter_id,
        invited_email=invitation.invited_email,
        token=invitation.token,
        accepted_at=invitation.accepted_at,
    )


def invite_to_club(group_id: int, inviter_id: int, invited_email: str) -> ClubInvitationResult:
    """Creates an invitation and emails the invite link.

    Raises:
        NotFoundError: if the group or inviter does not exist.
        InvitationNotAllowedError: if the inviter isn't a member of
            the group, or the invited email already belongs to a
            current member of this group.
    """
    normalized_email = normalize_email(invited_email)

    with get_session() as session:
        group = session.get(Group, group_id)
        if group is None:
            raise NotFoundError(f"Group {group_id} does not exist.")
        inviter = session.get(User, inviter_id)
        if inviter is None:
            raise NotFoundError(f"User {inviter_id} does not exist.")

        inviter_membership = session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == inviter_id, GroupMembership.group_id == group_id
            )
        )
        if inviter_membership is None:
            raise InvitationNotAllowedError(
                f"User {inviter_id} is not a member of group {group_id}."
            )

        existing_user = session.scalar(select(User).where(User.email == normalized_email))
        if existing_user is not None:
            existing_membership = session.scalar(
                select(GroupMembership).where(
                    GroupMembership.user_id == existing_user.id,
                    GroupMembership.group_id == group_id,
                )
            )
            if existing_membership is not None:
                raise InvitationNotAllowedError(
                    f"{normalized_email} is already a member of this club."
                )

        token_value = secrets.token_urlsafe(32)
        invitation = ClubInvitation(
            group_id=group_id,
            inviter_id=inviter_id,
            invited_email=normalized_email,
            token=token_value,
            expires_at=utcnow() + dt.timedelta(days=_INVITATION_VALID_DAYS),
        )
        session.add(invitation)
        session.flush()

        invite_link = f"{settings.app_base_url}/join-invitation/{token_value}"
        send_email(
            to_email=normalized_email,
            subject=f"{inviter.display_name} invited you to join {group.name} — The Diodati Debtors",
            html_body=(
                f"<p>{inviter.display_name} has invited you to join their book club, "
                f'"{group.name}", on The Diodati Debtors.</p>'
                f'<p><a href="{invite_link}">{invite_link}</a></p>'
                f"<p>This invitation expires in {_INVITATION_VALID_DAYS} days.</p>"
            ),
        )

        return _to_result(invitation)


def get_invitation(token: str) -> ClubInvitationResult:
    """Raises NotFoundError if the token doesn't exist."""
    with get_session() as session:
        invitation = session.scalar(select(ClubInvitation).where(ClubInvitation.token == token))
        if invitation is None:
            raise NotFoundError("This invitation does not exist.")
        return _to_result(invitation)

def accept_invitation(token: str, accepting_user_id: int) -> None:
    """Accepts an invitation, creating the GroupMembership directly —
    no separate JoinRequest/founder-approval step, since being
    invited by an existing member already constitutes trust, unlike
    a stranger requesting to join unprompted.

    Raises:
        NotFoundError: if the token or accepting user does not exist.
        InvitationNotAllowedError: if the invitation was already
            accepted, or has expired.
    """
    with get_session() as session:
        invitation = session.scalar(select(ClubInvitation).where(ClubInvitation.token == token))
        if invitation is None:
            raise NotFoundError("This invitation does not exist.")
        if invitation.accepted_at is not None:
            raise InvitationNotAllowedError("This invitation has already been used.")
        if invitation.expires_at < utcnow():
            raise InvitationNotAllowedError("This invitation has expired.")

        user = session.get(User, accepting_user_id)
        if user is None:
            raise NotFoundError(f"User {accepting_user_id} does not exist.")

        existing_membership = session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == accepting_user_id,
                GroupMembership.group_id == invitation.group_id,
            )
        )
        if existing_membership is None:
            membership = GroupMembership(
                user_id=accepting_user_id,
                group_id=invitation.group_id,
                role=GroupRole.MEMBER,
            )
            session.add(membership)

        invitation.accepted_at = utcnow()
        session.flush()


__all__ = [
    "ClubInvitationResult",
    "InvitationNotAllowedError",
    "invite_to_club",
    "get_invitation",
    "accept_invitation",
]