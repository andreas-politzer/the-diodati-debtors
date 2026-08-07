"""Authorization guards shared across services — small, cross-cutting
rules that don't belong to any single bounded context. Per the 03.08.
architecture decision (project vault): email verification enforcement
lives here, called explicitly by every service action that requires
it, rather than scattered checks or decorators in State/UI.
"""

from __future__ import annotations

from ..core.exceptions import EmailNotVerifiedError
from ..db.session import get_session
from ..models.user import User
from sqlalchemy import select
from ..models.group import GroupMembership


def require_verified_email(user_id: int) -> None:
    """Raises EmailNotVerifiedError if the user hasn't confirmed their
    email address yet. Silently passes for a nonexistent user_id —
    callers are expected to have already validated the user exists
    via their own NotFoundError checks; this guard's only concern is
    the verification flag."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is not None and not user.email_verified:
            raise EmailNotVerifiedError(
                "Please verify your email address before performing this action."
            )


def can_view_book(session, user_id: int, book) -> bool:
    """Same visibility rule used across the app: the book's owner, or
    anyone in a group the owner belongs to. Moved here from
    post_service.py (07.08. security review, project vault) — shared
    across multiple services, not a single-context implementation
    detail."""
    if book.owner_id == user_id:
        return True
    owner_group_ids = {
        m.group_id
        for m in session.scalars(
            select(GroupMembership).where(GroupMembership.user_id == book.owner_id)
        ).all()
    }
    if not owner_group_ids:
        return False
    return (
        session.scalar(
            select(GroupMembership).where(
                GroupMembership.user_id == user_id,
                GroupMembership.group_id.in_(owner_group_ids),
            )
        )
        is not None
    )


__all__ = ["require_verified_email", "can_view_book"]