"""Tests for group_service: founder invariant, join-request workflow,
authorization boundary, and the double-membership race condition fix.
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import (
    AlreadyGroupMemberError,
    DuplicateJoinRequestError,
    NotAuthorizedError,
    NotFoundError,
    RequestNotPendingError,
)
from diodati_debtors.models.enums import GroupRole, RequestStatus
from diodati_debtors.models.group import GroupMembership
from diodati_debtors.models.user import User
from diodati_debtors.services import group_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_create_group_sets_founder_invariant(db):
    founder_id = _make_user(db, "founder@example.com")

    result = group_service.create_group(founder_id=founder_id, name="Gothic Novel Society")

    with db() as session:
        membership = session.query(GroupMembership).filter_by(
            user_id=founder_id, group_id=result.id
        ).one()
        assert membership.role == GroupRole.FOUNDER


def test_create_group_rejects_blank_name(db):
    founder_id = _make_user(db, "founder2@example.com")

    with pytest.raises(Exception):  # InvalidGroupDataError
        group_service.create_group(founder_id=founder_id, name="   ")


def test_create_group_rejects_unknown_founder(db):
    with pytest.raises(NotFoundError):
        group_service.create_group(founder_id=999, name="Some Club")


def test_request_to_join_succeeds(db):
    founder_id = _make_user(db, "founder3@example.com")
    joiner_id = _make_user(db, "joiner@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club A")

    result = group_service.request_to_join(user_id=joiner_id, group_id=group.id)

    assert result.status == RequestStatus.PENDING.value


def test_request_to_join_rejects_existing_member(db):
    founder_id = _make_user(db, "founder4@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club B")

    with pytest.raises(AlreadyGroupMemberError):
        group_service.request_to_join(user_id=founder_id, group_id=group.id)


def test_request_to_join_rejects_duplicate_pending_request(db):
    founder_id = _make_user(db, "founder5@example.com")
    joiner_id = _make_user(db, "joiner2@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club C")

    group_service.request_to_join(user_id=joiner_id, group_id=group.id)

    with pytest.raises(DuplicateJoinRequestError):
        group_service.request_to_join(user_id=joiner_id, group_id=group.id)


def test_approve_join_request_creates_membership(db):
    founder_id = _make_user(db, "founder6@example.com")
    joiner_id = _make_user(db, "joiner3@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club D")
    request = group_service.request_to_join(user_id=joiner_id, group_id=group.id)

    result = group_service.approve_join_request(request.id, reviewer_id=founder_id)

    assert result.status == RequestStatus.APPROVED.value
    with db() as session:
        membership = session.query(GroupMembership).filter_by(
            user_id=joiner_id, group_id=group.id
        ).one()
        assert membership.role == GroupRole.MEMBER


def test_approve_join_request_rejects_non_founder_reviewer(db):
    founder_id = _make_user(db, "founder7@example.com")
    joiner_id = _make_user(db, "joiner4@example.com")
    outsider_id = _make_user(db, "outsider@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club E")
    request = group_service.request_to_join(user_id=joiner_id, group_id=group.id)

    with pytest.raises(NotAuthorizedError):
        group_service.approve_join_request(request.id, reviewer_id=outsider_id)


def test_approve_join_request_rejects_already_reviewed(db):
    founder_id = _make_user(db, "founder8@example.com")
    joiner_id = _make_user(db, "joiner5@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club F")
    request = group_service.request_to_join(user_id=joiner_id, group_id=group.id)
    group_service.approve_join_request(request.id, reviewer_id=founder_id)

    with pytest.raises(RequestNotPendingError):
        group_service.approve_join_request(request.id, reviewer_id=founder_id)


def test_approve_join_request_rejects_when_already_member(db):
    """Covers Codex's race-condition fix: if a membership already
    exists by the time approval happens (e.g. an admin added the user
    directly in the meantime), approval must fail cleanly, not via a
    raw database IntegrityError.
    """
    founder_id = _make_user(db, "founder9@example.com")
    joiner_id = _make_user(db, "joiner6@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club G")
    request = group_service.request_to_join(user_id=joiner_id, group_id=group.id)

    # Simulate an admin adding the user directly while the request is
    # still pending.
    with db() as session:
        session.add(
            GroupMembership(user_id=joiner_id, group_id=group.id, role=GroupRole.MEMBER)
        )
        session.commit()

    with pytest.raises(AlreadyGroupMemberError):
        group_service.approve_join_request(request.id, reviewer_id=founder_id)


def test_decline_join_request_creates_no_membership(db):
    founder_id = _make_user(db, "founder10@example.com")
    joiner_id = _make_user(db, "joiner7@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club H")
    request = group_service.request_to_join(user_id=joiner_id, group_id=group.id)

    result = group_service.decline_join_request(request.id, reviewer_id=founder_id)

    assert result.status == RequestStatus.DECLINED.value
    with db() as session:
        count = session.query(GroupMembership).filter_by(
            user_id=joiner_id, group_id=group.id
        ).count()
        assert count == 0

def test_update_group_description_succeeds(db):
    founder_id = _make_user(db, "founder11@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club I")

    result = group_service.update_group_description(
        group.id, founder_id=founder_id, description="We read 18th-century French literature."
    )

    assert result.description == "We read 18th-century French literature."


def test_update_group_description_rejects_non_founder(db):
    founder_id = _make_user(db, "founder12@example.com")
    outsider_id = _make_user(db, "outsider2@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club J")

    with pytest.raises(NotAuthorizedError):
        group_service.update_group_description(
            group.id, founder_id=outsider_id, description="Trying to sneak in a description."
        )


def test_update_group_description_normalizes_blank_to_none(db):
    founder_id = _make_user(db, "founder13@example.com")
    group = group_service.create_group(founder_id=founder_id, name="Club K")

    result = group_service.update_group_description(
        group.id, founder_id=founder_id, description="   "
    )

    assert result.description is None


def test_group_service_has_no_reflex_dependency():
    with open(group_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source