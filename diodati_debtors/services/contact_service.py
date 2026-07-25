"""Contact service — a personal, non-registered borrower (see
Domain Model, "External Contacts", project vault). Private to its
owner, never shared. No delete function exists — once created, a
contact stays, same philosophy as Book/Loan (existing loan history
must never be orphaned).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import InvalidContactDataError, NotAuthorizedError, NotFoundError
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.contact import Contact
from ..models.user import User


@dataclass(frozen=True)
class ContactResult:
    id: int
    owner_id: int
    name: str
    phone: str | None
    email: str | None
    address: str | None
    notes: str | None
    created_at: dt.datetime

    def to_dict(self) -> dict:
        return asdict(self)


def _to_result(contact: Contact) -> ContactResult:
    return ContactResult(
        id=contact.id,
        owner_id=contact.owner_id,
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        address=contact.address,
        notes=contact.notes,
        created_at=contact.created_at,
    )


def create_contact(
    owner_id: int,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    notes: str | None = None,
) -> ContactResult:
    """Raises: NotFoundError, InvalidContactDataError."""
    stripped_name = blank_to_none(name)
    if stripped_name is None:
        raise InvalidContactDataError("Contact name must not be blank.")

    with get_session() as session:
        owner = session.get(User, owner_id)
        if owner is None:
            raise NotFoundError(f"User {owner_id} does not exist.")

        contact = Contact(
            owner_id=owner_id,
            name=stripped_name,
            phone=blank_to_none(phone),
            email=blank_to_none(email),
            address=blank_to_none(address),
            notes=blank_to_none(notes),
        )
        session.add(contact)
        session.flush()
        return _to_result(contact)


def update_contact(
    contact_id: int,
    owner_id: int,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    notes: str | None = None,
) -> ContactResult:
    """Owner-only. Every field can change over time (e.g. grandmother
    moves) — only the record itself is never deleted.

    Raises:
        NotFoundError: if the contact does not exist.
        NotAuthorizedError: if owner_id does not own the contact.
        InvalidContactDataError: if name is blank.
    """
    stripped_name = blank_to_none(name)
    if stripped_name is None:
        raise InvalidContactDataError("Contact name must not be blank.")

    with get_session() as session:
        contact = session.get(Contact, contact_id)
        if contact is None:
            raise NotFoundError(f"Contact {contact_id} does not exist.")
        if contact.owner_id != owner_id:
            raise NotAuthorizedError(f"User {owner_id} does not own contact {contact_id}.")

        contact.name = stripped_name
        contact.phone = blank_to_none(phone)
        contact.email = blank_to_none(email)
        contact.address = blank_to_none(address)
        contact.notes = blank_to_none(notes)
        session.flush()
        return _to_result(contact)


def get_contact(contact_id: int) -> ContactResult:
    with get_session() as session:
        contact = session.get(Contact, contact_id)
        if contact is None:
            raise NotFoundError(f"Contact {contact_id} does not exist.")
        return _to_result(contact)


def list_contacts_for_owner(owner_id: int) -> list[ContactResult]:
    with get_session() as session:
        contacts = session.scalars(
            select(Contact).where(Contact.owner_id == owner_id).order_by(Contact.name)
        ).all()
        return [_to_result(c) for c in contacts]


__all__ = [
    "ContactResult",
    "create_contact",
    "update_contact",
    "get_contact",
    "list_contacts_for_owner",
]