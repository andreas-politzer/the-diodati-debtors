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

    ADVENTURE = "adventure"
    BIOGRAPHY = "biography"
    CHILDRENS = "childrens"
    CLASSIC = "classic"
    CONTEMPORARY = "contemporary"
    CRIME = "crime"
    DRAMA = "drama"
    DYSTOPIA_UTOPIA = "dystopia_utopia"
    ESSAY = "essay"
    FAIRY_TALE = "fairy_tale"
    FANTASY = "fantasy"
    GRAPHIC_NOVEL = "graphic_novel"
    HISTORICAL_FICTION = "historical_fiction"
    HISTORY = "history"
    HORROR = "horror"
    LITERARY_FICTION = "literary_fiction"
    MEMOIR = "memoir"
    MYSTERY = "mystery"
    NONFICTION = "nonfiction"
    PHILOSOPHY = "philosophy"
    POETRY = "poetry"
    ROMANCE = "romance"
    SATIRE = "satire"
    SCIENCE = "science"
    SCIENCE_FICTION = "science_fiction"
    THRILLER = "thriller"
    YOUNG_ADULT = "young_adult"


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

class PostType(str, enum.Enum):
    """Purely presentational — icon/color/filter in the UI, never
    changes a Post's lifecycle or database structure. The raven motif
    (messenger/bearer of news) is reserved for ANNOUNCEMENT.
    """

    GENERAL = "general"
    QUESTION = "question"
    ANNOUNCEMENT = "announcement"

class SummarySource(str, enum.Enum):
    """Where a book's summary came from — shown transparently in the
    UI, not hidden. The owner can always overwrite any source with
    their own text.
    """

    OWNER = "owner"
    OPEN_LIBRARY = "open_library"
    AI_GENERATED = "ai_generated"


__all__ = ["GroupRole", "RequestStatus", "BookGenre", "PostType", "SummarySource"]