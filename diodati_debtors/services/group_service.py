"""Group service — club creation, membership, and the join-request
workflow. Per the Service Contract: plain inputs, dataclass return
values, domain exceptions, self-contained transactions, no Reflex
import.

Founder invariant (Domain Model v2, project vault): a group's founder
always has a GroupMembership with role == FOUNDER. Enforced here,
atomically, in create_group() — never left to the caller to set up
separately.

JoinRequest is a distinct entity from GroupMembership, never deleted
on approval (immutable history, same principle as Loan/LoanRequest).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import (
    AlreadyGroupMemberError,
    DuplicateJoinRequestError,
    InvalidGroupDataError,
    NotAuthorizedError,
    NotFoundError,
    RequestNotPendingError,
)
from ..core.normalize import blank_to_none
from ..core.time import utcnow
from ..db.session import get_session
from ..models.enums import GroupRole, RequestStatus
from ..models.group import Group, GroupMembership
from ..models.join_request import JoinRequest
from ..models.user import User
from sqlalchemy.exc import IntegrityError


@dataclass(frozen=True)
class GroupResult:
    id: int
    name: str
    founder_id: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class JoinRequestResult:
    id: int
    user_id: int
    group_id: int
    status: str
    requested_at: dt.datetime
    reviewed_at: dt.datetime | None
    reviewed_by: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def _to_group_result(group: Group) -> GroupResult:
    return GroupResult(id=group.id, name=group.name, founder_id=group.founder_id)


def _to_join_request_result(request: JoinRequest) -> JoinRequestResult:
    return JoinRequestResult(
        id=request.id,
        user_id=request.user_id,
        group_id=request.group_id,
        status=request.status.value,
        requested_at=request.requested_at,
        reviewed_at=request.reviewed_at,
        reviewed_by=request.reviewed_by,
    )


def create_group(founder_id: int, name: str) -> GroupResult:
    """Found a new group. Atomically creates the Group and the
    founder's GroupMembership(role=FOUNDER) in one transaction — the
    founder invariant must never be satisfiable "later".

    Raises:
        NotFoundError: if founder_id does not exist.
        InvalidGroupDataError: if name is blank.
    """
    stripped_name = blank_to_none(name)
    if stripped_name is None:
        raise InvalidGroupDataError("Group name must not be blank.")

    with get_session() as session:
        founder = session.get(User, founder_id)
        if founder is None:
            raise NotFoundError(f"User {founder_id} does not exist.")

        group = Group(name=stripped_name, founder_id=founder_id)
        session.add(group)
        session.flush()

        session.add(
            GroupMembership(
                user_id=founder_id, group_id=group.id, role=GroupRole.FOUNDER
            )
        )
        session.flush()
        return _to_group_result(group)


def get_group(group_id: int) -> GroupResult:
    with get_session() as session:
        group = session.get(Group, group_id)
        if group is None:
            raise NotFoundError(f"Group {group_id} does not exist.")
        return _to_group_result(group)


def list_groups() -> list[GroupResult]:
    """All groups in the system — used for e.g. a "browse clubs to
    join" view. Not scoped to any particular user.
    """
    with get_session() as session:
        groups = session.scalars(select(Group).order_by(Group.name)).all()
        return [_to_group_result(g) for g in groups]


def list_groups_for_user(user_id: int) -> list[GroupResult]:
    """Groups the given user is currently a member of."""
    with get_session() as session:
        groups = session.scalars(
            select(Group)
            .join(GroupMembership, GroupMembership.group_id == Group.id)
            .where(GroupMembership.user_id == user_id)
            .order_by(Group.name)
        ).all()
        return [_to_group_result(g) for g in groups]


def request_to_join(user_id: int, group_id: int) -> JoinRequestResult:
    """Submit a request to join a group.

    Raises:
        NotFoundError: if the user or group does not exist.
        AlreadyGroupMemberError: if the user is already a member.
        DuplicateJoinRequestError: if a PENDING request already exists
            for this user/group pair.
    """
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} does not exist.")
        group = session.get(Group, group_id)
        if group is None:
            raise NotFoundError(f"Group {group_id} does not exist.")

        existing_membership = session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == user_id,
                GroupMembership.group_id == group_id,
            )
        )
        if existing_membership is not None:
            raise AlreadyGroupMemberError(
                f"User {user_id} is already a member of group {group_id}."
            )

        pending_request = session.scalar(
            select(JoinRequest).where(
                JoinRequest.user_id == user_id,
                JoinRequest.group_id == group_id,
                JoinRequest.status == RequestStatus.PENDING,
            )
        )
        if pending_request is not None:
            raise DuplicateJoinRequestError(
                f"User {user_id} already has a pending request for group {group_id}."
            )

        request = JoinRequest(user_id=user_id, group_id=group_id)
        session.add(request)
        session.flush()
        return _to_join_request_result(request)


def list_pending_join_requests_for_group(group_id: int) -> list[JoinRequestResult]:
    """Pending join requests for a group — feeds a future admin inbox."""
    with get_session() as session:
        requests = session.scalars(
            select(JoinRequest)
            .where(
                JoinRequest.group_id == group_id,
                JoinRequest.status == RequestStatus.PENDING,
            )
            .order_by(JoinRequest.requested_at)
        ).all()
        return [_to_join_request_result(r) for r in requests]


def _ensure_can_review(session, group_id: int, reviewer_id: int) -> None:
    """Only a group's founder may approve/decline join requests today.
    Multi-admin support (GroupRole.ADMIN reviewing too) is a documented
    future extension, not implemented yet.
    """
    membership = session.scalar(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == reviewer_id,
        )
    )
    if membership is None or membership.role != GroupRole.FOUNDER:
        raise NotAuthorizedError(
            f"User {reviewer_id} is not authorized to review requests for group {group_id}."
        )


def approve_join_request(request_id: int, reviewer_id: int) -> JoinRequestResult:
    """Approve a pending join request, creating the resulting
    GroupMembership. The request row itself is never deleted —
    immutable history, same as Loan/LoanRequest.

    Raises:
        NotFoundError: if the request does not exist.
        NotAuthorizedError: if reviewer_id is not the group's founder.
        RequestNotPendingError: if the request isn't currently PENDING.
        AlreadyGroupMemberError: if a membership was already created in
            the meantime (parallel admin-add, race between concurrent
            requests, future invitation/import path) — checked
            explicitly here rather than letting the database's
            UniqueConstraint surface as a raw IntegrityError, per the
            Service Contract (business rules stay on the service layer).
    """
    with get_session() as session:
        request = session.get(JoinRequest, request_id)
        if request is None:
            raise NotFoundError(f"JoinRequest {request_id} does not exist.")

        _ensure_can_review(session, request.group_id, reviewer_id)

        if request.status != RequestStatus.PENDING:
            raise RequestNotPendingError(
                f"JoinRequest {request_id} is not pending (status={request.status})."
            )

        existing_membership = session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == request.user_id,
                GroupMembership.group_id == request.group_id,
            )
        )
        if existing_membership is not None:
            raise AlreadyGroupMemberError(
                f"User {request.user_id} is already a member of group "
                f"{request.group_id} (created outside this request, e.g. by "
                f"an admin, invitation, or a concurrent approval)."
            )

        request.status = RequestStatus.APPROVED
        request.reviewed_at = utcnow()
        request.reviewed_by = reviewer_id
        session.add(
            GroupMembership(
                user_id=request.user_id,
                group_id=request.group_id,
                role=GroupRole.MEMBER,
            )
        )
        try:
            session.flush()
        except IntegrityError as e:
            # Belt-and-suspenders against the TOCTOU race between the
            # SELECT check above and this INSERT: two concurrent
            # approvals could both pass the check before either
            # commits. Extremely unlikely at this project's scale
            # (small, trusted clubs), but the fix is cheap — translate
            # the database's UniqueConstraint violation into the same
            # domain exception as the normal check, so callers never
            # see a raw IntegrityError either way.
            session.rollback()
            raise AlreadyGroupMemberError(
                f"User {request.user_id} is already a member of group "
                f"{request.group_id} (race condition: concurrent approval)."
            ) from e
        return _to_join_request_result(request)


def decline_join_request(request_id: int, reviewer_id: int) -> JoinRequestResult:
    """Decline a pending join request. No membership is created.

    Raises:
        NotFoundError: if the request does not exist.
        NotAuthorizedError: if reviewer_id is not the group's founder.
        RequestNotPendingError: if the request isn't currently PENDING.
    """
    with get_session() as session:
        request = session.get(JoinRequest, request_id)
        if request is None:
            raise NotFoundError(f"JoinRequest {request_id} does not exist.")

        _ensure_can_review(session, request.group_id, reviewer_id)

        if request.status != RequestStatus.PENDING:
            raise RequestNotPendingError(
                f"JoinRequest {request_id} is not pending (status={request.status})."
            )

        request.status = RequestStatus.DECLINED
        request.reviewed_at = utcnow()
        request.reviewed_by = reviewer_id
        session.flush()
        return _to_join_request_result(request)


__all__ = [
    "GroupResult",
    "JoinRequestResult",
    "create_group",
    "get_group",
    "list_groups",
    "list_groups_for_user",
    "request_to_join",
    "list_pending_join_requests_for_group",
    "approve_join_request",
    "decline_join_request",
]