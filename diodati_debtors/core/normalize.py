"""Project-wide string normalization policy.

Convention: optional text fields represent "not provided" as NULL,
never as an empty or whitespace-only string. This keeps later queries
simple (IS NULL, not IS NULL OR = '') and avoids two competing
representations of "no value" in the same column.

Every service handling an optional string field should route it
through `blank_to_none()` before persistence. Email normalization
(lowercase + trimmed) is a project-wide rule, not an auth-specific one
— any future service touching an email address uses `normalize_email()`
so identity comparison stays consistent everywhere.
"""

from __future__ import annotations


def blank_to_none(value: str | None) -> str | None:
    """Strip whitespace; return None if the result is empty."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def normalize_email(email: str | None) -> str:
    """Lowercase and trim an email address. Returns "" for blank/None
    input — callers validate presence separately.
    """
    if email is None:
        return ""
    return email.strip().lower()


__all__ = ["blank_to_none", "normalize_email"]