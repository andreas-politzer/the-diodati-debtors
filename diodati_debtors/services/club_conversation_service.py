"""Club Conversation service — the "Club-Internal Messages" process
from the Personal Messages domain session (project vault): free-form
messaging between two members of the SAME club, requiring no book
context (unlike BorrowingInquiry). Gated only by the recipient's
profile visibility, never by content.

Domain rule (30.07., confirmed by Andy's WhatsApp analogy): unlike
BorrowingInquiry, there is no OPEN/CLOSED lifecycle here — one
ongoing conversation per (initiator, recipient, club) that simply
grows over time, exactly like a real messaging thread. No "closing"
concept.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..core.exceptions import NotAuthorizedError, NotFoundError
from ..db.session import get_session
from ..models.club_conversation import ClubConversation, ClubConversationMessage
from ..models.enums import ProfileVisibility
from ..models.group import GroupMembership
from ..models.user import User
from ..models.user_profile import UserProfile


class ConversationNotAllowedError(Exception):
    """Raised when two users are not both members of the same club,
    or the recipient's profile visibility does not permit contact."""


@dataclass(frozen=True)
class ClubMessageResult:
    id: int
    sender_id: int
    content: str
    sent_at: dt.datetime
    read_at: dt.datetime | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ClubConversationResult:
    id: int
    group_id: int
    initiator_id: int
    recipient_id: int
    created_at: dt.datetime
    messages: list[ClubMessageResult]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "initiator_id": self.initiator_id,
            "recipient_id": self.recipient_id,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages],
        }


def _to_message_result(message: ClubConversationMessage) -> ClubMessageResult:
    return ClubMessageResult(
        id=message.id,
        sender_id=message.sender_id,
        content=message.content,
        sent_at=message.sent_at,
        read_at=message.read_at,
    )


def _to_conversation_result(conversation: ClubConversation) -> ClubConversationResult:
    return ClubConversationResult(
        id=conversation.id,
        group_id=conversation.group_id,
        initiator_id=conversation.initiator_id,
        recipient_id=conversation.recipient_id,
        created_at=conversation.created_at,
        messages=[_to_message_result(m) for m in conversation.messages],
    )


def _shared_group_id(session, user_a: int, user_b: int) -> int | None:
    """Returns the group_id of a club both users belong to, or None
    if they share no club membership. If they share multiple clubs,
    returns the first found — callers that care about a SPECIFIC
    club should pass one in explicitly instead."""
    groups_a = {
        m.group_id
        for m in session.scalars(
            select(GroupMembership).where(GroupMembership.user_id == user_a)
        ).all()
    }
    groups_b = {
        m.group_id
        for m in session.scalars(
            select(GroupMembership).where(GroupMembership.user_id == user_b)
        ).all()
    }
    shared = groups_a & groups_b
    return next(iter(shared), None)


def send_message(initiator_id: int, recipient_id: int, message: str, group_id: int | None = None) -> ClubConversationResult:
    """Sends a message, reusing an existing conversation between
    these two users in this club if one exists, or creating a new
    one otherwise. If group_id is not given, uses any shared club
    between the two users.

    Raises:
        NotFoundError: if either user does not exist.
        ConversationNotAllowedError: if the two users share no club
            membership, or the recipient's profile is PRIVATE.
    """
    with get_session() as session:
        initiator = session.get(User, initiator_id)
        if initiator is None:
            raise NotFoundError(f"User {initiator_id} does not exist.")
        recipient = session.get(User, recipient_id)
        if recipient is None:
            raise NotFoundError(f"User {recipient_id} does not exist.")

        if group_id is not None:
            is_member_a = session.scalar(
                select(GroupMembership).where(
                    GroupMembership.user_id == initiator_id,
                    GroupMembership.group_id == group_id,
                )
            )
            is_member_b = session.scalar(
                select(GroupMembership).where(
                    GroupMembership.user_id == recipient_id,
                    GroupMembership.group_id == group_id,
                )
            )
            if is_member_a is None or is_member_b is None:
                raise ConversationNotAllowedError(
                    f"Users {initiator_id} and {recipient_id} are not both "
                    f"members of group {group_id}."
                )
            resolved_group_id = group_id
        else:
            resolved_group_id = _shared_group_id(session, initiator_id, recipient_id)
            if resolved_group_id is None:
                raise ConversationNotAllowedError(
                    f"Users {initiator_id} and {recipient_id} share no club membership."
                )

        recipient_profile = session.query(UserProfile).filter_by(user_id=recipient_id).first()
        if recipient_profile is not None and recipient_profile.visibility == ProfileVisibility.PRIVATE:
            raise ConversationNotAllowedError(
                f"User {recipient_id} has set their profile to private."
            )

        conversation = session.scalar(
            select(ClubConversation).where(
                ClubConversation.group_id == resolved_group_id,
                (
                    (ClubConversation.initiator_id == initiator_id)
                    & (ClubConversation.recipient_id == recipient_id)
                )
                | (
                    (ClubConversation.initiator_id == recipient_id)
                    & (ClubConversation.recipient_id == initiator_id)
                ),
            )
        )
        if conversation is None:
            conversation = ClubConversation(
                group_id=resolved_group_id,
                initiator_id=initiator_id,
                recipient_id=recipient_id,
            )
            session.add(conversation)
            session.flush()

        new_message = ClubConversationMessage(
            conversation_id=conversation.id,
            sender_id=initiator_id,
            content=message,
        )
        session.add(new_message)
        session.flush()
        session.refresh(conversation)

        return _to_conversation_result(conversation)


def list_conversations_for_user(user_id: int) -> list[ClubConversationResult]:
    """All club conversations this user participates in, any club,
    ordered most recently active first."""
    with get_session() as session:
        conversations = session.scalars(
            select(ClubConversation)
            .where(
                (ClubConversation.initiator_id == user_id)
                | (ClubConversation.recipient_id == user_id)
            )
            .order_by(ClubConversation.created_at.desc())
        ).all()
        return [_to_conversation_result(c) for c in conversations]


def open_conversation(conversation_id: int, viewer_id: int) -> ClubConversationResult:
    """Opening a conversation marks all messages directed AT the
    viewer as read — same "reading is a side effect of viewing"
    principle as BorrowingInquiry.

    Raises:
        NotFoundError: if the conversation does not exist.
        NotAuthorizedError: if viewer_id is not a participant.
    """
    with get_session() as session:
        conversation = session.get(ClubConversation, conversation_id)
        if conversation is None:
            raise NotFoundError(f"ClubConversation {conversation_id} does not exist.")

        if viewer_id not in (conversation.initiator_id, conversation.recipient_id):
            raise NotAuthorizedError(
                f"User {viewer_id} is not a participant in conversation {conversation_id}."
            )

        now = dt.datetime.utcnow()
        for message in conversation.messages:
            if message.sender_id != viewer_id and message.read_at is None:
                message.read_at = now

        session.flush()
        session.refresh(conversation)

        return _to_conversation_result(conversation)


__all__ = [
    "ClubMessageResult",
    "ClubConversationResult",
    "ConversationNotAllowedError",
    "send_message",
    "list_conversations_for_user",
    "open_conversation",
]