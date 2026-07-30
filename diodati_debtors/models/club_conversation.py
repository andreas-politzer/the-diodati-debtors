"""ClubConversation — the "Club-Internal Messages" process from the
Personal Messages domain session (project vault): free-form messaging
between two members of the SAME club, gated only by the recipient's
profile visibility (never by content — the constraint lives in
context, not topic). No book required, unlike BorrowingInquiry.

Kept entirely separate from BorrowingInquiry — different fachlich
processes (this one requires shared club membership, not a specific
book match).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class ClubConversation(Base):
    __tablename__ = "club_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False, index=True
    )
    initiator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    group: Mapped["Group"] = relationship()
    initiator: Mapped["User"] = relationship(foreign_keys=[initiator_id])
    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_id])
    messages: Mapped[list["ClubConversationMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan",
        order_by="ClubConversationMessage.sent_at",
    )

    def __repr__(self) -> str:
        return f"<ClubConversation id={self.id} group_id={self.group_id}>"


class ClubConversationMessage(Base):
    __tablename__ = "club_conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("club_conversations.id"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    conversation: Mapped["ClubConversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<ClubConversationMessage id={self.id} conversation_id={self.conversation_id}>"


__all__ = ["ClubConversation", "ClubConversationMessage"]