"""Librarian Maintenance service — background "housekeeping" tasks
for the library's search infrastructure, deliberately separate from
user-facing write operations. Per the 07.08. architecture decision
(project vault): embeddings are search infrastructure, not part of
the book-creation write path — a book is fully created the moment
it's saved, independent of whether it's already semantically
searchable. This service is where the Librarian "does his own
inventory" periodically, rather than every write operation being
responsible for keeping the search index current.

Intended to be called by a periodic job (e.g. a Railway Cron Job),
not directly by user-facing State classes.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from ..db.session import get_session
from ..models.book import Book
from .book_service import compute_and_store_embedding


@dataclass(frozen=True)
class EmbeddingBackfillReport:
    total_checked: int
    succeeded: int
    failed: int


def backfill_missing_embeddings() -> EmbeddingBackfillReport:
    """Finds every book without an embedding and computes one. Safe to
    run repeatedly (idempotent — books that already have an embedding
    are simply skipped). A single failure never stops the rest of the
    batch, per the same "robust rather than strict" principle used
    elsewhere (e.g. Bulk Import)."""
    with get_session() as session:
        book_ids = session.scalars(
            select(Book.id).where(Book.embedding.is_(None))
        ).all()

    succeeded = 0
    failed = 0
    for book_id in book_ids:
        try:
            with get_session() as session:
                book = session.get(Book, book_id)
                if book is None:
                    continue
                compute_and_store_embedding(session, book)
                session.commit()
            succeeded += 1
        except Exception:
            failed += 1

    return EmbeddingBackfillReport(
        total_checked=len(book_ids), succeeded=succeeded, failed=failed
    )


__all__ = ["EmbeddingBackfillReport", "backfill_missing_embeddings"]