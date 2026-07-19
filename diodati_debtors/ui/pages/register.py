"""Register page — public, no auth required to view."""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import page_title
from ..components.shell import shell
from ..tokens import Color, Font, Type
from ...state.auth_state import AuthState


def register() -> rx.Component:
    return shell(
        page_title("Register"),
        rx.cond(
            AuthState.error_message != "",
            rx.text(
                AuthState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.form(
            rx.vstack(
                rx.input(placeholder="Display name", name="display_name", required=True),
                rx.input(placeholder="Email", name="email", type="email", required=True),
                rx.input(
                    placeholder="Password", name="password", type="password", required=True
                ),
                primary_button("Register", type="submit"),
                spacing="3",
            ),
            on_submit=AuthState.register,
            reset_on_submit=True,
        ),
        rx.link("☞ Log in instead", href="/login", margin_top="1rem", display="block"),
        max_width="28rem",
    )


__all__ = ["register"]