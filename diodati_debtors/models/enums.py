"""Domain enums shared across models.

Python enum.Enum, stored via SQLAlchemy with native_enum=False (plain
VARCHAR column, not a native MySQL ENUM type) — adding a new role or
status later is a code change, not an ALTER TABLE migration.
"""

from __future__ import annotations

import enum


class GroupRole(str, enum.Enum):
    """A member's role within a specific group. Explicit domain concept
    rather than an arbitrary string, per Codex's review — avoids
    scattered string comparisons for authorization logic.

    Invariant (enforced in group_service, not the database): the
    founder of a group always has a corresponding GroupMembership with
    role == FOUNDER.
    """

    FOUNDER = "founder"
    ADMIN = "admin"
    MEMBER = "member"


class RequestStatus(str, enum.Enum):
    """Shared status vocabulary for JoinRequest and LoanRequest. Not a
    generic Request abstraction (the two remain separate tables per
    the domain model) — just the same small set of outcome words,
    which is a coincidence of vocabulary, not shared behaviour.

    APPROVED rows are never deleted or "consumed" once the
    corresponding Membership/Loan is created — they remain
    indefinitely as an audit trail, same immutable-history principle
    as Loan itself.

    EXPIRED exists now so a future automatic-expiry feature doesn't
    need an enum migration — no expiry logic is implemented today.
    """

    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


__all__ = ["GroupRole", "RequestStatus"]