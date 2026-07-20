"""Group state — the adapter between Reflex UI and group_service.

Separate from LibraryState and AuthState per Codex's bounded-context
guidance.

Needs AuthState.current_user_id — accessed via the async get_state()
pattern, since these are two separate top-level State classes.

current_group_id persists via cookie so a page reload doesn't reset
which club is "active".

group_options is a computed var derived from my_groups, not a
separately-maintained field — one source of truth, no risk of the two
falling out of sync (per Andy's review).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import group_service
from .auth_state import AuthState


@dataclass
class MemberEntry:
    user_id: int
    display_name: str
    role: str


@dataclass
class ClubMembersView:
    group_id: int
    group_name: str
    members: list[MemberEntry] = field(default_factory=list)


class GroupState(rx.State):
    my_groups: list[dict] = []
    available_groups: list[dict] = []
    club_members: list[ClubMembersView] = []
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

    @rx.var
    def group_options(self) -> list[str]:
        """Flat "id: name" strings for rx.select pickers — derived
        from my_groups, never separately maintained.
        """
        return [f"{g['id']}: {g['name']}" for g in self.my_groups]

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

        my_group_ids = {g["id"] for g in self.my_groups}

        # The cookie is browser-scoped, not user-scoped — a stale
        # selection from a previous login (different user, same
        # browser) must never be treated as valid for this user.
        if self.current_group_id and int(self.current_group_id) not in my_group_ids:
            self.current_group_id = ""

        if not self.current_group_id and len(self.my_groups) == 1:
            self.current_group_id = str(self.my_groups[0]["id"])

    async def load_available_groups(self):
        try:
            groups = group_service.list_groups()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        my_group_ids = {g["id"] for g in self.my_groups}
        self.available_groups = [
            g.to_dict() for g in groups if g.id not in my_group_ids
        ]

    async def load_members_overview(self):
        """Members grouped by every club the current user belongs to
        — not just the currently-selected one (Andy's review: needs
        to answer "who's in which of MY clubs", not just one at a time).
        """
        self.error_message = ""
        if not self.my_groups:
            await self.load_my_groups()

        overview: list[ClubMembersView] = []
        for group in self.my_groups:
            try:
                members = group_service.list_members(group["id"])
            except DiodatiError as e:
                self.error_message = str(e)
                continue
            overview.append(
                ClubMembersView(
                    group_id=group["id"],
                    group_name=group["name"],
                    members=[
                        MemberEntry(
                            user_id=m.user_id, display_name=m.display_name, role=m.role
                        )
                        for m in members
                    ],
                )
            )
        self.club_members = overview

    async def load_all(self):
        await self.load_my_groups()
        await self.load_available_groups()

    def select_group(self, group_id):
        self.current_group_id = str(group_id)
        return rx.redirect("/dashboard")

    def switch_group(self, selected_option: str):
        """Switch the active club directly from the dashboard, no
        detour through /clubs.
        """
        try:
            group_id = int(selected_option.split(":", 1)[0].strip())
        except (ValueError, IndexError):
            return
        self.current_group_id = str(group_id)

    def check_group_selected(self):
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
    
    def clear_selection(self):
        """Clear all club-related state — called on logout so a stale
        club selection never leaks into the next user's session on
        the same browser.
        """
        self.current_group_id = ""
        self.my_groups = []
        self.available_groups = []
        self.club_members = []

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

    async def update_description(self, form_data: dict):
        self.error_message = ""
        self.info_message = ""
        if not self.current_group_id:
            self.error_message = "No club selected."
            return
        auth_state = await self.get_state(AuthState)
        try:
            group_service.update_group_description(
                int(self.current_group_id),
                founder_id=int(auth_state.current_user_id),
                description=form_data.get("description", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.info_message = "Description updated."
        await self.load_my_groups()


__all__ = ["GroupState", "MemberEntry", "ClubMembersView"]