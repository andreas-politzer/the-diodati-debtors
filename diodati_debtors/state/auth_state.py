"""Auth state — the adapter between Reflex UI and auth_service.

Separate from LibraryState per Codex's bounded-context guidance.

Only the user id persists in a cookie — email and display name are
loaded from user_service on demand, never duplicated into cookies.
Stored as a string, not int — Reflex Cookies are string-backed under
the hood, and comparing an int-typed Cookie against a literal 0
produced a type-mismatch warning that made is_logged_in always
evaluate True.
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import auth_service, user_service


class AuthState(rx.State):
    current_user_id: str = rx.Cookie("", name="diodati_user_id")
    error_message: str = ""

    @rx.var
    def is_logged_in(self) -> bool:
        return self.current_user_id != ""

    @rx.var(cache=True)
    def current_user_display_name(self) -> str:
        """Loaded on demand from user_service — never cached in a
        cookie, so it's always current.
        """
        if not self.current_user_id:
            return ""
        try:
            return user_service.get_user(int(self.current_user_id)).display_name
        except (DiodatiError, ValueError):
            return ""

    def check_auth(self):
        """Shared guard for protected pages: use as an on_load handler."""
        if not self.is_logged_in:
            return rx.redirect("/login")

    def redirect_if_logged_in(self):
        """Guard for public-only pages (login, register)."""
        if self.is_logged_in:
            return rx.redirect("/dashboard")

    def register(self, form_data: dict):
        self.error_message = ""
        try:
            result = auth_service.register(
                email=form_data.get("email", ""),
                password=form_data.get("password", ""),
                display_name=form_data.get("display_name", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.current_user_id = str(result.id)
        return rx.redirect("/dashboard")

    def login(self, form_data: dict):
        self.error_message = ""
        try:
            result = auth_service.login(
                email=form_data.get("email", ""),
                password=form_data.get("password", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.current_user_id = str(result.id)
        return rx.redirect("/dashboard")

    def logout(self):
        self.current_user_id = ""
        return rx.redirect("/")


__all__ = ["AuthState"]