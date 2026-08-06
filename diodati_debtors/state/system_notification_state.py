"""System Notification state — powers a small, dismissible popup on
the Dashboard for unread system messages (e.g. the welcome message
after email verification/invitation acceptance).
"""

from __future__ import annotations

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import system_notification_service
from .auth_state import AuthState


class SystemNotificationState(rx.State):
    unread_title: str = ""
    unread_content: str = ""
    unread_id: int = 0
    show_popup: bool = False

    async def load_notifications(self):
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.show_popup = False
            return

        try:
            notifications = system_notification_service.list_notifications_for_user(
                int(auth_state.current_user_id)
            )
        except DiodatiError:
            self.show_popup = False
            return

        unread = [n for n in notifications if n.read_at is None]
        if unread:
            latest = unread[0]
            self.unread_id = latest.id
            self.unread_title = latest.title
            self.unread_content = latest.content
            self.show_popup = True
        else:
            self.show_popup = False

    async def dismiss(self):
        auth_state = await self.get_state(AuthState)
        system_notification_service.mark_notification_read(
            self.unread_id, int(auth_state.current_user_id)
        )
        self.show_popup = False


__all__ = ["SystemNotificationState"]