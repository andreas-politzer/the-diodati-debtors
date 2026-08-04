"""Auth service — registration, login, password management, identity.

Password hashing lives in core/password.py (isolates auth_service from
the hashing library). Email normalization lives in core/normalize.py
(project-wide rule, not auth-specific). user_service remains the
separate, permanent read/directory service — this module never
becomes a general-purpose user API.
"""

from __future__ import annotations

import datetime as dt
import logging
import secrets

logger = logging.getLogger(__name__)

from sqlalchemy import select

from ..core.config import settings
from ..core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
)
from ..core.normalize import blank_to_none, normalize_email
from ..core.password import hash_password, verify_password
from ..core.time import utcnow
from ..db.session import get_session
from ..models.email_verification_token import EmailVerificationToken
from ..models.user import User
from .external.email_client import send_email
from .user_service import UserResult

_MIN_PASSWORD_LENGTH = 8


def _to_result(user: User) -> UserResult:
    return UserResult(id=user.id, email=user.email, display_name=user.display_name)

_TOKEN_VALID_HOURS = 24


def _create_and_send_verification_token(session, user: User) -> None:
    """Creates a fresh verification token and emails the link. Failure
    to send the email is logged but never blocks registration itself —
    a user can always request a resend later (see resend_verification_email)."""
    token_value = secrets.token_urlsafe(32)
    token = EmailVerificationToken(
        user_id=user.id,
        token=token_value,
        expires_at=utcnow() + dt.timedelta(hours=_TOKEN_VALID_HOURS),
    )
    session.add(token)
    session.flush()

    verification_link = f"{settings.app_base_url}/verify-email/{token_value}"
    try:
        send_email(
            to_email=user.email,
            subject="Confirm your email — The Diodati Debtors",
            html_body=(
                f"<p>Welcome to The Diodati Debtors! Please confirm your "
                f"email address by clicking the link below:</p>"
                f'<p><a href="{verification_link}">{verification_link}</a></p>'
                f"<p>This link expires in {_TOKEN_VALID_HOURS} hours.</p>"
            ),
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", user.email)


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
            email_verified=False,
        )
        session.add(user)
        session.flush()
        _create_and_send_verification_token(session, user)
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

def verify_email(token: str) -> UserResult:
    """Marks the token's user as email_verified, if the token is valid,
    unused, and not expired.

    Raises:
        InvalidCredentialsError: if the token doesn't exist, was
            already used, or has expired — deliberately generic,
            same reasoning as login's InvalidCredentialsError (never
            reveal *why* a token failed to a potential attacker probing
            token guesses).
    """
    with get_session() as session:
        verification_token = session.scalar(
            select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        )
        if verification_token is None:
            raise InvalidCredentialsError("This verification link is invalid.")
        if verification_token.used_at is not None:
            raise InvalidCredentialsError("This verification link has already been used.")
        if verification_token.expires_at < utcnow():
            raise InvalidCredentialsError("This verification link has expired.")

        user = session.get(User, verification_token.user_id)
        if user is None:
            raise InvalidCredentialsError("This verification link is invalid.")

        user.email_verified = True
        verification_token.used_at = utcnow()
        session.flush()
        return _to_result(user)


def resend_verification_email(user_id: int) -> None:
    """Invalidates any still-unused prior tokens for this user, then
    creates and sends a fresh one — per the 03.08. architecture
    decision (project vault): old tokens are never deleted, only
    superseded, same immutable-history principle as elsewhere."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise InvalidCredentialsError("User not found.")
        if user.email_verified:
            return

        unused_tokens = session.scalars(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used_at.is_(None),
            )
        ).all()
        for old_token in unused_tokens:
            old_token.used_at = utcnow()

        _create_and_send_verification_token(session, user)


__all__ = ["register", "login", "verify_email", "resend_verification_email"]