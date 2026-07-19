"""User service — read-only directory lookups.

Registration, login, and password handling belong to auth_service.
This module owns user lookup and read operations for the rest of the
application (directory, borrower selection, group membership views) —
a permanent, distinct responsibility from auth_service, not a
temporary Phase 2 helper.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..db.session import get_session
from ..models.user import User


@dataclass(frozen=True)
class UserResult:
    id: int
    email: str
    display_name: str

    def to_dict(self) -> dict:
        """Explicit serialization boundary — see loan_service.LoanResult
        for the same pattern and rationale.
        """
        return asdict(self)


def _to_result(user: User) -> UserResult:
    return UserResult(id=user.id, email=user.email, display_name=user.display_name)


def list_users() -> list[UserResult]:
    """List all users, ordered by display name."""
    with get_session() as session:
        users = session.scalars(select(User).order_by(User.display_name)).all()
        return [_to_result(user) for user in users]


__all__ = ["UserResult", "list_users"]