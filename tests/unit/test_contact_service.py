"""Tests for contact_service: owner-only updates, name validation,
no delete function (by design)."""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import (
    InvalidContactDataError,
    NotAuthorizedError,
    NotFoundError,
)
from diodati_debtors.models.user import User
from diodati_debtors.services import contact_service


def _make_user(db, email: str, *, verified: bool = True) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User", email_verified=verified)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_create_contact_succeeds(db):
    owner_id = _make_user(db, "owner1@example.com")

    result = contact_service.create_contact(
        owner_id=owner_id, name="Grandma", phone="12345", notes="Prefers hardcover."
    )

    assert result.name == "Grandma"
    assert result.phone == "12345"
    assert result.notes == "Prefers hardcover."


def test_create_contact_rejects_blank_name(db):
    owner_id = _make_user(db, "owner2@example.com")

    with pytest.raises(InvalidContactDataError):
        contact_service.create_contact(owner_id=owner_id, name="   ")


def test_update_contact_succeeds_for_owner(db):
    owner_id = _make_user(db, "owner3@example.com")
    contact = contact_service.create_contact(owner_id=owner_id, name="Neighbour")

    result = contact_service.update_contact(
        contact.id, owner_id=owner_id, name="Neighbour", address="New address"
    )

    assert result.address == "New address"


def test_update_contact_rejects_non_owner(db):
    owner_id = _make_user(db, "owner4@example.com")
    outsider_id = _make_user(db, "outsider1@example.com")
    contact = contact_service.create_contact(owner_id=owner_id, name="Friend")

    with pytest.raises(NotAuthorizedError):
        contact_service.update_contact(contact.id, owner_id=outsider_id, name="Hijacked")


def test_list_contacts_for_owner_returns_only_that_owners_contacts(db):
    owner_id = _make_user(db, "owner5@example.com")
    other_owner_id = _make_user(db, "owner6@example.com")
    contact_service.create_contact(owner_id=owner_id, name="My Contact")
    contact_service.create_contact(owner_id=other_owner_id, name="Their Contact")

    results = contact_service.list_contacts_for_owner(owner_id)

    assert [c.name for c in results] == ["My Contact"]


def test_contact_service_has_no_reflex_dependency():
    with open(contact_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source