"""Tests for profile_service — the optional UserProfile layer."""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import NotFoundError
from diodati_debtors.models.user import User
from diodati_debtors.services import profile_service


def _make_user(db, email: str, *, verified: bool = True) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User", email_verified=verified)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_get_or_create_profile_creates_with_defaults(db):
    user_id = _make_user(db, "profile1@example.com")

    result = profile_service.get_or_create_profile(user_id)

    assert result.user_id == user_id
    assert result.display_name is None
    assert result.visibility == "clubs_only"


def test_get_or_create_profile_returns_existing_on_second_call(db):
    user_id = _make_user(db, "profile2@example.com")

    profile_service.update_profile(user_id, display_name="Andy")
    result = profile_service.get_or_create_profile(user_id)

    assert result.display_name == "Andy"


def test_get_or_create_profile_raises_for_unknown_user(db):
    with pytest.raises(NotFoundError):
        profile_service.get_or_create_profile(999999)


def test_update_profile_sets_all_fields(db):
    user_id = _make_user(db, "profile3@example.com")

    result = profile_service.update_profile(
        user_id,
        display_name="Andy P.",
        location="Hamburg",
        bio="Love gothic novels.",
        favorite_genre="horror",
        visibility="public",
    )

    assert result.display_name == "Andy P."
    assert result.location == "Hamburg"
    assert result.bio == "Love gothic novels."
    assert result.favorite_genre == "horror"
    assert result.visibility == "public"


def test_update_profile_normalizes_blank_fields_to_none(db):
    user_id = _make_user(db, "profile4@example.com")

    result = profile_service.update_profile(user_id, display_name="   ", bio="")

    assert result.display_name is None
    assert result.bio is None


def test_update_profile_raises_for_unknown_user(db):
    with pytest.raises(NotFoundError):
        profile_service.update_profile(999999, display_name="Ghost")

def test_get_public_profile_user_ids_returns_only_public(db):
    public_user_id = _make_user(db, "public_profile1@example.com")
    private_user_id = _make_user(db, "private_profile1@example.com")
    clubs_only_user_id = _make_user(db, "clubsonly_profile1@example.com")

    profile_service.update_profile(public_user_id, visibility="public")
    profile_service.update_profile(private_user_id, visibility="private")
    profile_service.update_profile(clubs_only_user_id, visibility="clubs_only")

    result = profile_service.get_public_profile_user_ids(
        [public_user_id, private_user_id, clubs_only_user_id]
    )

    assert result == {public_user_id}


def test_get_public_profile_user_ids_returns_empty_for_no_profiles(db):
    user_id = _make_user(db, "no_profile1@example.com")

    result = profile_service.get_public_profile_user_ids([user_id])

    assert result == set()


def test_get_public_profile_user_ids_returns_empty_set_for_empty_input():
    result = profile_service.get_public_profile_user_ids([])

    assert result == set()


def test_profile_service_has_no_reflex_dependency():
    with open(profile_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source