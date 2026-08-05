"""System Notification service — one-way messages from the platform
itself to a user. Deliberately separate from ClubConversation/
BorrowingInquiry (per the 04.08. architecture decision, project
vault): a system message isn't a person-to-person conversation and
shouldn't force a second real user or club membership to exist.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from ..db.session import get_session
from ..models.system_notification import SystemNotification
from ..core.time import utcnow


@dataclass(frozen=True)
class SystemNotificationResult:
    id: int
    title: str
    content: str
    created_at: object
    read_at: object | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at,
            "read_at": self.read_at,
        }


def _to_result(notification: SystemNotification) -> SystemNotificationResult:
    return SystemNotificationResult(
        id=notification.id,
        title=notification.title,
        content=notification.content,
        created_at=notification.created_at,
        read_at=notification.read_at,
    )


def send_welcome_notification(user_id: int) -> SystemNotificationResult:
    """Sends the one-time welcome message after a user's first
    successful email verification."""
    with get_session() as session:
        notification = SystemNotification(
            user_id=user_id,
            title="Welcome to The Diodati Debtors",
            content=(
                "Your account has been verified successfully. You can "
                "now join clubs, lend books, and become part of the "
                "community."
            ),
        )
        session.add(notification)
        session.flush()
        return _to_result(notification)


def list_notifications_for_user(user_id: int) -> list[SystemNotificationResult]:
    with get_session() as session:
        notifications = session.scalars(
            select(SystemNotification)
            .where(SystemNotification.user_id == user_id)
            .order_by(SystemNotification.created_at.desc())
        ).all()
        return [_to_result(n) for n in notifications]


def count_unread_notifications(user_id: int) -> int:
    with get_session() as session:
        notifications = session.scalars(
            select(SystemNotification).where(
                SystemNotification.user_id == user_id,
                SystemNotification.read_at.is_(None),
            )
        ).all()
        return len(notifications)


def mark_notification_read(notification_id: int, user_id: int) -> None:
    with get_session() as session:
        notification = session.get(SystemNotification, notification_id)
        if notification is None or notification.user_id != user_id:
            return
        if notification.read_at is None:
            notification.read_at = utcnow()
            session.flush()


__all__ = [
    "SystemNotificationResult",
    "send_welcome_notification",
    "list_notifications_for_user",
    "count_unread_notifications",
    "mark_notification_read",
]