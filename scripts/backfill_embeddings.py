"""One-off script: compute embeddings for every existing book that
doesn't have one yet (books created before the embedding feature
existed). Safe to re-run — skips books that already have an
embedding.
"""

from __future__ import annotations

from sqlalchemy import select

from diodati_debtors.db.session import get_session
from diodati_debtors.models.book import Book
from diodati_debtors.services.book_service import _compute_and_store_embedding


def main():
    with get_session() as session:
        books = session.scalars(select(Book).where(Book.embedding.is_(None))).all()
        print(f"Found {len(books)} books without an embedding.")
        for book in books:
            print(f"Computing embedding for: {book.title}")
            _compute_and_store_embedding(session, book)
        session.commit()
        print("Done.")


if __name__ == "__main__":
    main()