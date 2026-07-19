"""Password hashing — isolates the hashing library from the service
layer. If the algorithm or library ever changes, only this module
needs to change, not auth_service.

Uses bcrypt directly rather than via passlib: passlib's bcrypt backend
detection is incompatible with modern bcrypt (>=4.1) releases — a
known, unresolved passlib/bcrypt version mismatch (passlib is
effectively unmaintained). Using bcrypt directly avoids that broken
detection path entirely, with a smaller, more transparent API.
"""

from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


__all__ = ["hash_password", "verify_password"]