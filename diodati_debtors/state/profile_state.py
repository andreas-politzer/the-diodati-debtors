"""Profile state — the adapter between Reflex UI and profile_service.
Separate bounded context, own state class, per the project's
established discipline.
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import profile_service, trust_service
from .auth_state import AuthState


class ProfileState(rx.State):
    display_name: str = ""
    reliability: str = ""
    book_care: str = ""
    location: str = ""
    bio: str = ""
    favorite_genre: str = ""
    avatar_url: str = ""
    visibility: str = "clubs_only"

    error_message: str = ""
    info_message: str = ""

    def set_display_name(self, value: str):
        self.display_name = value

    def set_location(self, value: str):
        self.location = value

    def set_bio(self, value: str):
        self.bio = value

    def set_favorite_genre(self, value: str):
        self.favorite_genre = value

    def set_visibility(self, value: str):
        self.visibility = value

    async def load_profile(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            return
        try:
            profile = profile_service.get_or_create_profile(int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.display_name = profile.display_name or ""
        self.location = profile.location or ""
        self.bio = profile.bio or ""
        self.favorite_genre = profile.favorite_genre or ""
        self.avatar_url = profile.avatar_url or ""
        self.visibility = profile.visibility
        signals = trust_service.get_trust_signals(int(auth_state.current_user_id))
        self.reliability = signals.reliability
        self.book_care = signals.book_care

    @rx.var
    async def initials(self) -> str:
        name = self.display_name.strip()
        if not name:
            auth_state = await self.get_state(AuthState)
            name = auth_state.current_user_display_name.strip()
        parts = [p for p in name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][0].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    async def save_profile(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return

        try:
            profile_service.update_profile(
                int(auth_state.current_user_id),
                display_name=self.display_name,
                location=self.location,
                bio=self.bio,
                favorite_genre=self.favorite_genre,
                visibility=self.visibility,
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.info_message = "Profile saved."

    async def reset_profile(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return

        try:
            profile_service.update_profile(
                int(auth_state.current_user_id),
                display_name="",
                location="",
                bio="",
                favorite_genre="",
                visibility="clubs_only",
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.display_name = ""
        self.location = ""
        self.bio = ""
        self.favorite_genre = ""
        self.visibility = "clubs_only"
        self.info_message = "Profile reset to defaults."


__all__ = ["ProfileState"]