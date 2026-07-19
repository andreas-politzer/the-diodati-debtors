"""Seed demo data.

Exercises the same service functions a real user would trigger — book
creation goes through book_service.create_book, loans go through
loan_service.create_loan/return_loan — so this script is not a
parallel, hand-rolled data path that could drift from real behaviour.
It just automates the same actions a person would take by hand.

User creation and group/membership setup go directly through the ORM,
since auth_service (registration, password hashing) is deferred until
Phase 3 — password_hash below is a clearly-labelled placeholder, not a
real hash. Login will not function until auth_service exists.

Covers all core domain states in one compact dataset, per Codex's
review: an available book, an active loan, a returned loan, and a user
belonging to multiple groups (demonstrating the Kicktipp-style
multi-club dropdown).

This script is destructive: it truncates existing demo data before
reseeding (not DELETE — TRUNCATE also resets MySQL's auto-increment
counters, so repeated runs produce the same deterministic primary keys,
per Codex's review). It refuses to run unless DIODATI_DEBUG is enabled,
as a guard against accidental use against a non-development database.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from diodati_debtors.core.config import settings
from diodati_debtors.db.session import get_session
from diodati_debtors.services import book_service, loan_service

PLACEHOLDER_PASSWORD_HASH = "seed-placeholder-not-a-real-hash"
REFERENCE_DATE = dt.date(2026, 7, 1)

_TABLES_IN_TRUNCATE_ORDER = [
    "posts",
    "loans",
    "group_memberships",
    "books",
    "users",
    "groups",
]


def _truncate_all_demo_tables() -> None:
    """TRUNCATE, not DELETE — resets MySQL's auto-increment counters so
    repeated seed runs produce identical, deterministic primary keys.
    Foreign key checks are disabled only for the duration of this call.

    Table names are backtick-quoted because `groups` is a reserved
    word in MySQL 8.0+ (GROUPS BETWEEN window-frame syntax).
    """
    with get_session() as session:
        session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in _TABLES_IN_TRUNCATE_ORDER:
            session.execute(text(f"TRUNCATE TABLE `{table}`"))
        session.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def _make_user(email: str, display_name: str) -> int:
    from diodati_debtors.models.user import User

    with get_session() as session:
        user = User(
            email=email,
            password_hash=PLACEHOLDER_PASSWORD_HASH,
            display_name=display_name,
        )
        session.add(user)
        session.flush()
        return user.id


def _make_group(name: str) -> int:
    from diodati_debtors.models.group import Group

    with get_session() as session:
        group = Group(name=name)
        session.add(group)
        session.flush()
        return group.id


def _add_membership(user_id: int, group_id: int) -> None:
    from diodati_debtors.models.group import GroupMembership

    with get_session() as session:
        session.add(GroupMembership(user_id=user_id, group_id=group_id))


def seed() -> None:
    if not settings.debug:
        raise RuntimeError(
            "Refusing to seed demo data: DIODATI_DEBUG is not enabled. "
            "This script is for local development only."
        )

    _truncate_all_demo_tables()

    # Groups — three clubs to demonstrate the multi-club login dropdown.
    diodati_id = _make_group("The Diodati Debtors")
    romantics_id = _make_group("Late Romantics Reading Circle")
    gothic_id = _make_group("Gothic Novel Society")

    # Users — Liane and Andy each belong to two clubs, demonstrating
    # multi-membership (one User row, several GroupMemberships).
    liane_id = _make_user("liane@example.com", "Liane")
    fabian_id = _make_user("fabian@example.com", "Fabian")
    andy_id = _make_user("andy@example.com", "Andy")

    _add_membership(liane_id, diodati_id)
    _add_membership(liane_id, romantics_id)
    _add_membership(fabian_id, diodati_id)
    _add_membership(andy_id, diodati_id)
    _add_membership(andy_id, gothic_id)

    # Books — created through book_service, exactly as a user would.
    frankenstein = book_service.create_book(
        owner_id=liane_id, title="Frankenstein", author="Mary Shelley"
    )
    dracula = book_service.create_book(
        owner_id=fabian_id, title="Dracula", author="Bram Stoker"
    )
    book_service.create_book(
        owner_id=andy_id, title="The Vampyre", author="John Polidori"
    )  # stays available — no loan created for this one

    # Loans — through loan_service, covering the states Codex flagged:
    # available (Vampyre, untouched above), active loan, returned loan.
    loan_service.create_loan(
        book_id=frankenstein.id,
        borrower_id=fabian_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14),
        loan_date=REFERENCE_DATE,
    )

    returned = loan_service.create_loan(
        book_id=dracula.id,
        borrower_id=andy_id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14),
        loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(
        returned.id, return_date=REFERENCE_DATE + dt.timedelta(days=5)
    )

    print("Seed complete:")
    print("  Groups: The Diodati Debtors, Late Romantics Reading Circle, Gothic Novel Society")
    print("  Users: Liane (2 clubs), Fabian (1 club), Andy (2 clubs)")
    print("  Books: Frankenstein (on loan), Dracula (returned), The Vampyre (available)")


if __name__ == "__main__":
    seed()