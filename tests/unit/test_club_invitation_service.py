"""Tests for club_invitation_service — the full ClubInvitation
domain workflow (create + accept), per the 04.08. architecture
decision (project vault): domain vs. delivery-channel adapter.
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import NotFoundError
from diodati_debtors.models.group import Group, GroupMembership
from diodati_debtors.models.enums import GroupRole
from diodati_debtors.models.user import User
from diodati_debtors.services import club_invitation_service


def _make_user(db, email: str, *, verified: bool = True) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User", email_verified=verified)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_group_with_founder(db, founder_id: int, name: str) -> int:
    with db() as session:
        group = Group(name=name, founder_id=founder_id)
        session.add(group)
        session.commit()
        session.refresh(group)
        membership = GroupMembership(user_id=founder_id, group_id=group.id, role=GroupRole.FOUNDER)
        session.add(membership)
        session.commit()
        return group.id


def test_invite_to_club_creates_invitation(db):
    founder_id = _make_user(db, "founder_inv1@example.com")
    group_id = _make_group_with_founder(db, founder_id, "Gothic Club")

    result = club_invitation_service.invite_to_club(group_id, founder_id, "friend_inv1@example.com")

    assert result.group_id == group_id
    assert result.invited_email == "friend_inv1@example.com"
    assert result.accepted_at is None


def test_invite_to_club_rejects_non_member_inviter(db):
    founder_id = _make_user(db, "founder_inv2@example.com")
    outsider_id = _make_user(db, "outsider_inv1@example.com")
    group_id = _make_group_with_founder(db, founder_id, "Gothic Club 2")

    with pytest.raises(club_invitation_service.InvitationNotAllowedError):
        club_invitation_service.invite_to_club(group_id, outsider_id, "friend_inv2@example.com")


def test_invite_to_club_rejects_already_a_member(db):
    founder_id = _make_user(db, "founder_inv3@example.com")
    member_id = _make_user(db, "member_inv1@example.com")
    group_id = _make_group_with_founder(db, founder_id, "Gothic Club 3")
    with db() as session:
        session.add(GroupMembership(user_id=member_id, group_id=group_id, role=GroupRole.MEMBER))
        session.commit()

    with pytest.raises(club_invitation_service.InvitationNotAllowedError):
        club_invitation_service.invite_to_club(group_id, founder_id, "member_inv1@example.com")


def test_accept_invitation_creates_membership(db):
    founder_id = _make_user(db, "founder_inv4@example.com")
    group_id = _make_group_with_founder(db, founder_id, "Gothic Club 4")
    invitee_id = _make_user(db, "friend_inv3@example.com")
    invitation = club_invitation_service.invite_to_club(group_id, founder_id, "friend_inv3@example.com")

    club_invitation_service.accept_invitation(invitation.token, invitee_id)

    with db() as session:
        membership = session.query(GroupMembership).filter_by(
            user_id=invitee_id, group_id=group_id
        ).first()
        assert membership is not None
        assert membership.role == GroupRole.MEMBER


def test_accept_invitation_rejects_already_used(db):
    founder_id = _make_user(db, "founder_inv5@example.com")
    group_id = _make_group_with_founder(db, founder_id, "Gothic Club 5")
    invitee_id = _make_user(db, "friend_inv4@example.com")
    invitation = club_invitation_service.invite_to_club(group_id, founder_id, "friend_inv4@example.com")
    club_invitation_service.accept_invitation(invitation.token, invitee_id)

    with pytest.raises(club_invitation_service.InvitationNotAllowedError):
        club_invitation_service.accept_invitation(invitation.token, invitee_id)


def test_accept_invitation_rejects_unknown_token(db):
    invitee_id = _make_user(db, "friend_inv5@example.com")

    with pytest.raises(NotFoundError):
        club_invitation_service.accept_invitation("nonexistent-token", invitee_id)


def test_get_invitation_rejects_unknown_token():
    with pytest.raises(NotFoundError):
        club_invitation_service.get_invitation("nonexistent-token")


def test_club_invitation_service_has_no_reflex_dependency():
    with open(club_invitation_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source