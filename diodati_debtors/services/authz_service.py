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


__all__ = ["require_verified_email"]