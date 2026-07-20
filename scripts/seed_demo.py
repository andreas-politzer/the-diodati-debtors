"""Seed demo data.

Exercises the same service functions a real user would trigger — book
creation goes through book_service.create_book, loans go through
loan_service.create_loan/return_loan — so this script is not a
parallel, hand-rolled data path that could drift from real behaviour.
It just automates the same actions a person would take by hand.

User/Group/GroupMembership creation goes directly through the ORM,
since auth_service (registration) exists but group_service does not
yet — password_hash below is a clearly-labelled placeholder, not a
real hash for the demo users' actual passwords.

Founder invariant (Domain Model v2, project vault): a group's founder
always has a GroupMembership with role == FOUNDER. Enforced here by
hand until group_service exists to enforce it atomically.

This script is destructive: it truncates existing demo data before
reseeding (not DELETE — TRUNCATE also resets MySQL's auto-increment
counters, so repeated runs produce identical, deterministic primary
keys). It refuses to run unless DIODATI_DEBUG is enabled, as a guard
against accidental use against a non-development database.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from diodati_debtors.core.config import settings
from diodati_debtors.db.session import get_session
from diodati_debtors.models.enums import GroupRole
from diodati_debtors.services import book_service, loan_service

PLACEHOLDER_PASSWORD_HASH = "seed-placeholder-not-a-real-hash"
REFERENCE_DATE = dt.date(2026, 7, 1)

_TABLES_IN_TRUNCATE_ORDER = [
    "posts",
    "loan_requests",
    "join_requests",
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


def _make_group(name: str, founder_id: int) -> int:
    from diodati_debtors.models.group import Group

    with get_session() as session:
        group = Group(name=name, founder_id=founder_id)
        session.add(group)
        session.flush()
        return group.id


def _add_membership(user_id: int, group_id: int, role: GroupRole = GroupRole.MEMBER) -> None:
    from diodati_debtors.models.group import GroupMembership

    with get_session() as session:
        session.add(GroupMembership(user_id=user_id, group_id=group_id, role=role))


def seed() -> None:
    if not settings.debug:
        raise RuntimeError(
            "Refusing to seed demo data: DIODATI_DEBUG is not enabled. "
            "This script is for local development only."
        )

    _truncate_all_demo_tables()

    # Users first — groups need a founder_id before they can be created.
    liane_id = _make_user("liane@example.com", "Liane")
    fabian_id = _make_user("fabian@example.com", "Fabian")
    andy_id = _make_user("andy@example.com", "Andy")

    # Groups — Liane founds the two she's most active in, Andy founds
    # his own. Each founder gets a FOUNDER membership (the invariant
    # from Domain Model v2), everyone else gets MEMBER.
    diodati_id = _make_group("The Diodati Debtors", founder_id=liane_id)
    romantics_id = _make_group("Late Romantics Reading Circle", founder_id=liane_id)
    gothic_id = _make_group("Gothic Novel Society", founder_id=andy_id)

    _add_membership(liane_id, diodati_id, role=GroupRole.FOUNDER)
    _add_membership(liane_id, romantics_id, role=GroupRole.FOUNDER)
    _add_membership(fabian_id, diodati_id, role=GroupRole.MEMBER)
    _add_membership(andy_id, diodati_id, role=GroupRole.MEMBER)
    _add_membership(andy_id, gothic_id, role=GroupRole.FOUNDER)

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

    # Loans — through loan_service, covering available/active/returned.
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
    print("  Groups: The Diodati Debtors (founder: Liane), Late Romantics Reading Circle (founder: Liane), Gothic Novel Society (founder: Andy)")
    print("  Users: Liane (2 clubs, founder of both), Fabian (1 club), Andy (2 clubs, founder of one)")
    print("  Books: Frankenstein (on loan), Dracula (returned), The Vampyre (available)")


if __name__ == "__main__":
    seed()