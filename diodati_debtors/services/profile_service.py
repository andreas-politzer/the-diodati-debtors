"""Profile service — the entirely optional UserProfile layer on top
of the mandatory User account. Per the Service Contract: plain
inputs, dataclass return values, domain exceptions, no Reflex import.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..core.exceptions import NotFoundError
from ..core.normalize import blank_to_none
from ..db.session import get_session
from ..models.enums import ProfileVisibility
from ..models.user import User
from ..models.user_profile import UserProfile
from sqlalchemy import select


@dataclass(frozen=True)
class ProfileResult:
    user_id: int
    display_name: str | None
    location: str | None
    bio: str | None
    favorite_genre: str | None
    avatar_url: str | None
    visibility: str

    def to_dict(self) -> dict:
        return asdict(self)


def _to_result(profile: UserProfile) -> ProfileResult:
    return ProfileResult(
        user_id=profile.user_id,
        display_name=profile.display_name,
        location=profile.location,
        bio=profile.bio,
        favorite_genre=profile.favorite_genre,
        avatar_url=profile.avatar_url,
        visibility=profile.visibility.value,
    )


def get_or_create_profile(user_id: int) -> ProfileResult:
    """Every user effectively "has" a profile — created lazily on
    first access with sensible defaults (all fields empty,
    CLUBS_ONLY visibility), rather than requiring an explicit setup
    step before the profile page can render.

    Raises:
        NotFoundError: if the user does not exist.
    """
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} does not exist.")

        profile = session.query(UserProfile).filter_by(user_id=user_id).first()

        if profile is None:
            profile = UserProfile(user_id=user_id, visibility=ProfileVisibility.CLUBS_ONLY)
            session.add(profile)
            session.flush()

        return _to_result(profile)


def update_profile(
    user_id: int,
    display_name: str | None = None,
    location: str | None = None,
    bio: str | None = None,
    favorite_genre: str | None = None,
    avatar_url: str | None = None,
    visibility: str | None = None,
) -> ProfileResult:
    """Updates the caller's own profile. Every field is optional and
    independently overwritable — blank strings normalize to None
    (a field left empty means "no info given", not "empty string").

    Raises:
        NotFoundError: if the user does not exist.
        InvalidBookDataError: (reused) if visibility is not a valid
            ProfileVisibility value.
    """
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} does not exist.")

        profile = session.query(UserProfile).filter_by(user_id=user_id).first()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            session.add(profile)

        profile.display_name = blank_to_none(display_name)
        profile.location = blank_to_none(location)
        profile.bio = blank_to_none(bio)
        profile.favorite_genre = blank_to_none(favorite_genre)
        profile.avatar_url = blank_to_none(avatar_url)
        if visibility is not None:
            profile.visibility = ProfileVisibility(visibility)

        session.flush()
        return _to_result(profile)

def get_public_profile_user_ids(user_ids: list[int]) -> set[int]:
    """Given a list of user IDs, returns the subset whose profile
    visibility is PUBLIC — used to decide whether a name should be
    clickable/linked in the Global Board or Club Feed (per the 31.07.
    domain session: a name only becomes a link as a natural
    consequence of having posted, never through a separate directory).
    """
    if not user_ids:
        return set()

    with get_session() as session:
        profiles = session.scalars(
            select(UserProfile).where(
                UserProfile.user_id.in_(user_ids),
                UserProfile.visibility == ProfileVisibility.PUBLIC,
            )
        ).all()
        return {p.user_id for p in profiles}


__all__ = ["ProfileResult", "get_or_create_profile", "update_profile"]