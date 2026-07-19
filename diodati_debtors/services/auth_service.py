"""Auth service — registration, login, password management, identity.

Password hashing lives in core/password.py (isolates auth_service from
the hashing library). Email normalization lives in core/normalize.py
(project-wide rule, not auth-specific). user_service remains the
separate, permanent read/directory service — this module never
becomes a general-purpose user API.
"""

from __future__ import annotations

from sqlalchemy import select

from ..core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
)
from ..core.normalize import blank_to_none, normalize_email
from ..core.password import hash_password, verify_password
from ..db.session import get_session
from ..models.user import User
from .user_service import UserResult

_MIN_PASSWORD_LENGTH = 8


def _to_result(user: User) -> UserResult:
    return UserResult(id=user.id, email=user.email, display_name=user.display_name)


def register(email: str, password: str, display_name: str) -> UserResult:
    """Register a new user.

    Raises:
        InvalidRegistrationDataError: if any field is blank, the email
            looks invalid, or the password is shorter than the minimum
            length.
        EmailAlreadyRegisteredError: if the (normalized) email is
            already registered.
    """
    normalized_email = normalize_email(email)
    stripped_name = blank_to_none(display_name)

    if not normalized_email or "@" not in normalized_email:
        raise InvalidRegistrationDataError("A valid email is required.")
    if stripped_name is None:
        raise InvalidRegistrationDataError("Display name must not be blank.")
    if not password or len(password) < _MIN_PASSWORD_LENGTH:
        raise InvalidRegistrationDataError(
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
        )

    with get_session() as session:
        existing = session.scalar(select(User).where(User.email == normalized_email))
        if existing is not None:
            raise EmailAlreadyRegisteredError(
                f"Email {normalized_email} is already registered."
            )

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=stripped_name,
        )
        session.add(user)
        session.flush()
        return _to_result(user)


def login(email: str, password: str) -> UserResult:
    """Verify credentials and return the authenticated user.

    Raises:
        InvalidCredentialsError: if the email/password combination is
            invalid. Deliberately generic — never distinguishes
            "no such email" from "wrong password", to avoid leaking
            whether an account exists.
    """
    normalized_email = normalize_email(email)

    with get_session() as session:
        user = session.scalar(select(User).where(User.email == normalized_email))
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        return _to_result(user)


__all__ = ["register", "login"]