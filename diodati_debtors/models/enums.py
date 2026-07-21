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

class BookGenre(str, enum.Enum):
    """Predefined genre vocabulary — a flat, pragmatic browsing list,
    not an academic taxonomy (deliberately mixes genre and literary
    form, per the "goal is browsing, not classification" principle).
    Single genre per book in V1 — a future many-to-many extension
    remains possible without redesigning this.
    """

    FANTASY = "fantasy"
    SCIENCE_FICTION = "science_fiction"
    HORROR = "horror"
    MYSTERY = "mystery"
    THRILLER = "thriller"
    HISTORICAL_FICTION = "historical_fiction"
    LITERARY_FICTION = "literary_fiction"
    ROMANCE = "romance"
    ADVENTURE = "adventure"
    DYSTOPIA_UTOPIA = "dystopia_utopia"
    BIOGRAPHY = "biography"
    HISTORY = "history"
    SCIENCE = "science"
    PHILOSOPHY = "philosophy"
    NONFICTION = "nonfiction"
    POETRY = "poetry"
    DRAMA = "drama"
    ESSAY = "essay"
    YOUNG_ADULT = "young_adult"
    CHILDRENS = "childrens"
    FAIRY_TALE = "fairy_tale"
    SATIRE = "satire"


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


__all__ = ["GroupRole", "RequestStatus", "BookGenre"]