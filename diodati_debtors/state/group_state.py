"""Group state — the adapter between Reflex UI and group_service.

Separate from LibraryState and AuthState per Codex's bounded-context
guidance: club membership/selection is its own domain, distinct from
books/loans (LibraryState) and identity (AuthState).

Needs AuthState.current_user_id — accessed via the async get_state()
pattern, since these are two separate top-level State classes, not a
parent/substate relationship.

current_group_id persists via cookie (like AuthState.current_user_id)
so a page reload doesn't reset which club is "active".
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import group_service
from .auth_state import AuthState


class GroupState(rx.State):
    my_groups: list[dict] = []
    available_groups: list[dict] = []
    current_group_id: str = rx.Cookie("", name="diodati_group_id")
    error_message: str = ""
    info_message: str = ""

    @rx.var
    def has_groups(self) -> bool:
        return len(self.my_groups) > 0

    @rx.var
    def current_group_name(self) -> str:
        for g in self.my_groups:
            if str(g["id"]) == self.current_group_id:
                return g["name"]
        return ""

    async def load_my_groups(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            return
        try:
            groups = group_service.list_groups_for_user(int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.my_groups = [g.to_dict() for g in groups]

        # If nothing is selected yet but the user has exactly one
        # club, select it automatically — avoids an unnecessary extra
        # click for the common case.
        if not self.current_group_id and len(self.my_groups) == 1:
            self.current_group_id = str(self.my_groups[0]["id"])

    async def load_available_groups(self):
        """Only clubs the user is NOT already a member of — otherwise
        "Request to join" on an existing club just produces an
        AlreadyGroupMemberError from the service, which is correct but
        needlessly confusing (Codex's review). Assumes load_my_groups()
        has already populated self.my_groups (see load_all order).
        """
        try:
            groups = group_service.list_groups()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        my_group_ids = {g["id"] for g in self.my_groups}
        self.available_groups = [
            g.to_dict() for g in groups if g.id not in my_group_ids
        ]
    async def load_all(self):
        await self.load_my_groups()
        await self.load_available_groups()

    def select_group(self, group_id):
        self.current_group_id = str(group_id)
        return rx.redirect("/dashboard")

    def check_group_selected(self):
        """Guard for pages that require an active club selection —
        analogous to AuthState.check_auth."""
        if not self.current_group_id:
            return rx.redirect("/clubs")

    async def create_group(self, form_data: dict):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            result = group_service.create_group(
                founder_id=int(auth_state.current_user_id),
                name=form_data.get("name", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.current_group_id = str(result.id)
        return rx.redirect("/dashboard")

    async def send_join_request(self, group_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            group_service.request_to_join(
                user_id=int(auth_state.current_user_id), group_id=int(group_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Request sent — waiting for approval."


__all__ = ["GroupState"]