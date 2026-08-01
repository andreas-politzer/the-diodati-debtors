"""Profile page — the entirely optional second layer on top of the
mandatory Account. Per the Personal Messages domain session (project
vault): one shared visibility level for the whole profile, avatar is
initials-only (miniature-portrait style, no upload).
"""

from __future__ import annotations

import reflex as rx

from ..components.avatar import avatar
from ..components.button import primary_button, warning_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.auth_state import AuthState
from ...state.profile_state import ProfileState
from ...models.enums import BookGenre


def profile() -> rx.Component:
    return shell(
        page_title("My Profile"),
        avatar(ProfileState.initials),
        rx.hstack(
            meta_text(f"Reliability: {ProfileState.reliability}"),
            meta_text(f"Book Care: {ProfileState.book_care}"),
            spacing="3",
        ),
        divider(),
        divider(),
        rx.cond(
            ProfileState.error_message != "",
            rx.text(
                ProfileState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            ProfileState.info_message != "",
            meta_text(ProfileState.info_message),
        ),
        rx.vstack(
            rx.input(
                placeholder="Display name (optional)",
                value=ProfileState.display_name,
                on_change=ProfileState.set_display_name,
            ),
            rx.input(
                placeholder="Location, e.g. Hamburg (optional)",
                value=ProfileState.location,
                on_change=ProfileState.set_location,
            ),
            rx.text_area(
                placeholder="A short bio (optional)",
                value=ProfileState.bio,
                on_change=ProfileState.set_bio,
                rows="4",
            ),
            rx.vstack(
                meta_text("Favourite genre (optional)"),
                rx.select(
                    ["—"] + [g.value for g in BookGenre],
                    value=ProfileState.favorite_genre,
                    on_change=ProfileState.set_favorite_genre,
                ),
                spacing="1",
            ),
            rx.vstack(
                meta_text("Who can see this profile and contact you?"),
                rx.select(
                    ["private", "clubs_only", "public"],
                    value=ProfileState.visibility,
                    on_change=ProfileState.set_visibility,
                ),
                spacing="1",
            ),
            rx.hstack(
                primary_button("Save profile", on_click=ProfileState.save_profile, type="button"),
                warning_button("Reset to defaults", on_click=ProfileState.reset_profile, type="button"),
                spacing="3",
            ),
            spacing="3",
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["profile"]