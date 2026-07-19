"""Group and GroupMembership entities.

GroupMembership is the join table enabling one User to belong to
several Groups (the Kicktipp-style multi-club model agreed earlier).
A UniqueConstraint prevents the same user joining the same group twice.

GroupMembership is a pure dependent row — it has no meaning without its
User and Group, so it cascades on delete. Group itself has no cascade
toward Posts (ownership relation, service-layer decision).

Timestamps: see core/time.py for the project-wide UTC policy.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Intentionally not unique — two clubs may share a name.
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    memberships: Mapped[list["GroupMembership"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(back_populates="group")

    def __repr__(self) -> str:
        return f"<Group id={self.id} name={self.name!r}>"


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False, index=True
    )
    joined_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="memberships")
    group: Mapped["Group"] = relationship(back_populates="memberships")

    def __repr__(self) -> str:
        return f"<GroupMembership user_id={self.user_id} group_id={self.group_id}>"