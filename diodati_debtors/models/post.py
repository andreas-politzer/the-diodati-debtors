"""Post entity — schema only in Phase 2, no service or UI yet.

Represents a feed entry within a group: a recommendation, a question
("has anyone read X?"), or a "just finished this, happy to lend it"
announcement. Deferred to Phase 3 per Roadmap/Implementation
Specification — this model exists now only so the full ER diagram and
Alembic migration are complete in one pass.

Posts are intentionally immutable — no updated_at, no editing after
creation. Feed ordering must always use ORDER BY created_at at the
database level, never ORM insertion order.

Timestamps: see core/time.py for the project-wide UTC policy.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.time import utcnow
from ..db.base import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    author: Mapped["User"] = relationship(back_populates="posts")
    group: Mapped["Group"] = relationship(back_populates="posts")

    def __repr__(self) -> str:
        return f"<Post id={self.id} author_id={self.author_id}>"