"""Seed demo data — larger volume for manual testing across roles.

Registration goes through auth_service.register (real, working
passwords for every demo user, not a placeholder hash) — so you can
log in as any of them. Books go through book_service.create_book, one
call per book, still not a parallel hand-rolled data path.

Four users, each with ten books, spread across two clubs with
deliberate overlap (multi-club membership, founder vs. member roles),
a mix of active/returned loans, and one pending join request plus one
pending loan request already sitting in the Organize inbox for
immediate testing.

This script is destructive: it truncates existing demo data before
reseeding (not DELETE — TRUNCATE also resets MySQL's auto-increment
counters, so repeated runs produce identical, deterministic primary
keys). It refuses to run unless DIODATI_DEBUG is enabled, as a guard
against accidental use against a non-development database.

All demo users share the same password: "seeddemo123"
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
from diodati_debtors.services import auth_service, book_service, group_service, loan_service

DEMO_PASSWORD = "seeddemo123"
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

# 40 classic gothic/romantic-era titles, ten per demo user.
_BOOK_POOL = [
    ("Frankenstein", "Mary Shelley"),
    ("The Castle of Otranto", "Horace Walpole"),
    ("The Monk", "Matthew Lewis"),
    ("Vathek", "William Beckford"),
    ("Melmoth the Wanderer", "Charles Maturin"),
    ("The Mysteries of Udolpho", "Ann Radcliffe"),
    ("Northanger Abbey", "Jane Austen"),
    ("Wuthering Heights", "Emily Brontë"),
    ("Jane Eyre", "Charlotte Brontë"),
    ("The Turn of the Screw", "Henry James"),
    ("Dracula", "Bram Stoker"),
    ("The Vampyre", "John Polidori"),
    ("Carmilla", "Sheridan Le Fanu"),
    ("The Picture of Dorian Gray", "Oscar Wilde"),
    ("Strange Case of Dr Jekyll and Mr Hyde", "Robert Louis Stevenson"),
    ("The Fall of the House of Usher", "Edgar Allan Poe"),
    ("Great Expectations", "Charles Dickens"),
    ("Uncle Silas", "Sheridan Le Fanu"),
    ("The Woman in White", "Wilkie Collins"),
    ("The Moonstone", "Wilkie Collins"),
    ("Zofloya", "Charlotte Dacre"),
    ("The Italian", "Ann Radcliffe"),
    ("Frankenstein in Baghdad", "Ahmed Saadawi"),
    ("The Beetle", "Richard Marsh"),
    ("The Haunting of Hill House", "Shirley Jackson"),
    ("We Have Always Lived in the Castle", "Shirley Jackson"),
    ("Rebecca", "Daphne du Maurier"),
    ("The Historian", "Elizabeth Kostova"),
    ("Interview with the Vampire", "Anne Rice"),
    ("Something Wicked This Way Comes", "Ray Bradbury"),
    ("The Shadow over Innsmouth", "H. P. Lovecraft"),
    ("At the Mountains of Madness", "H. P. Lovecraft"),
    ("The King in Yellow", "Robert W. Chambers"),
    ("House of Leaves", "Mark Z. Danielewski"),
    ("The Wolf's Hour", "Robert R. McCammon"),
    ("Salem's Lot", "Stephen King"),
    ("The Shining", "Stephen King"),
    ("Coraline", "Neil Gaiman"),
    ("The Graveyard Book", "Neil Gaiman"),
    ("Mexican Gothic", "Silvia Moreno-Garcia"),
]


def _truncate_all_demo_tables() -> None:
    with get_session() as session:
        session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in _TABLES_IN_TRUNCATE_ORDER:
            session.execute(text(f"TRUNCATE TABLE `{table}`"))
        session.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def _add_membership(user_id: int, group_id: int, role: GroupRole) -> None:
    from diodati_debtors.models.group import GroupMembership

    with get_session() as session:
        session.add(GroupMembership(user_id=user_id, group_id=group_id, role=role))


def _add_ten_books(owner_id: int, start_index: int) -> list:
    titles = _BOOK_POOL[start_index : start_index + 10]
    return [
        book_service.create_book(owner_id=owner_id, title=title, author=author)
        for title, author in titles
    ]


def seed() -> None:
    if not settings.debug:
        raise RuntimeError(
            "Refusing to seed demo data: DIODATI_DEBUG is not enabled. "
            "This script is for local development only."
        )

    _truncate_all_demo_tables()

    # Users — real, working passwords via auth_service.
    liane = auth_service.register(email="liane@example.com", password=DEMO_PASSWORD, display_name="Liane")
    fabian = auth_service.register(email="fabian@example.com", password=DEMO_PASSWORD, display_name="Fabian")
    andy = auth_service.register(email="andy@example.com", password=DEMO_PASSWORD, display_name="Andy")
    marta = auth_service.register(email="marta@example.com", password=DEMO_PASSWORD, display_name="Marta")

    # Two clubs, deliberate overlap — Andy is founder of one, member of
    # the other, so both roles are directly testable.
    diodati = group_service.create_group(founder_id=liane.id, name="The Diodati Debtors")
    gothic = group_service.create_group(founder_id=andy.id, name="Gothic Novel Society")

    _add_membership(fabian.id, diodati.id, GroupRole.MEMBER)
    _add_membership(andy.id, diodati.id, GroupRole.MEMBER)
    _add_membership(fabian.id, gothic.id, GroupRole.MEMBER)

    # Ten books each.
    liane_books = _add_ten_books(liane.id, 0)
    fabian_books = _add_ten_books(fabian.id, 10)
    andy_books = _add_ten_books(andy.id, 20)
    marta_books = _add_ten_books(marta.id, 30)

    # A handful of loans — active and returned, across different owners/borrowers.
    loan_service.create_loan(
        book_id=liane_books[0].id, borrower_id=fabian.id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    returned = loan_service.create_loan(
        book_id=fabian_books[0].id, borrower_id=andy.id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )
    loan_service.return_loan(returned.id, return_date=REFERENCE_DATE + dt.timedelta(days=5))
    loan_service.create_loan(
        book_id=andy_books[0].id, borrower_id=marta.id,
        due_date=REFERENCE_DATE + dt.timedelta(days=14), loan_date=REFERENCE_DATE,
    )

    # Deliberately left PENDING — real material for the Organize inbox.
    group_service.request_to_join(user_id=marta.id, group_id=diodati.id)  # Liane can approve/decline
    loan_service.request_to_borrow(book_id=marta_books[1].id, requester_id=fabian.id)  # Marta can approve/decline

    print("Seed complete. All demo users share the password:", DEMO_PASSWORD)
    print()
    print("  liane@example.com  — founder of The Diodati Debtors, 10 books")
    print("  fabian@example.com — member of both clubs, 10 books")
    print("  andy@example.com   — founder of Gothic Novel Society, member of The Diodati Debtors, 10 books")
    print("  marta@example.com  — member of Gothic Novel Society, 10 books, has a pending join request to The Diodati Debtors")
    print()
    print("Pending in Organize inbox:")
    print("  Marta's join request to The Diodati Debtors — review as liane@example.com")
    print("  Fabian's loan request for one of Marta's books — review as marta@example.com")


if __name__ == "__main__":
    seed()