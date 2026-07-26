"""Librarian service — semantic search over books, with the discretion
principle built in from the start (see Ask the Librarian Vision,
project vault): a match outside the requester's visible scope (their
own books + fellow club members' books) is never revealed by title or
owner — only the club name is hinted, so the requester can ask to join.

Cosine similarity is computed in plain Python — no vector database
needed at our scale (a few hundred books at most). Single scoring
pass over all embedded books, then split by visibility — avoids
computing similarity twice (per ChatGPT's review).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass

from sqlalchemy import select

from .external.gemini_client import embed_text
from .group_service import get_visible_owner_ids
from ..db.session import get_session
from ..models.book import Book
from ..models.group import GroupMembership

MATCH_THRESHOLD = 0.75  # tunable without architecture changes — see Trust Signals for the same principle


@dataclass(frozen=True)
class LibrarianMatch:
    book_id: int
    title: str
    author: str | None
    similarity: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RestrictedHint:
    """A good match exists, but outside the requester's visible scope.
    Only club_name is revealed today — deliberately a value object
    (not a plain string) so it can grow later (e.g. invite_possible,
    member_count) without changing the public API."""

    club_name: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LibrarianResult:
    matches: list[LibrarianMatch]
    restricted_hint: RestrictedHint | None
    no_match_at_all: bool

    def to_dict(self) -> dict:
        return {
            "matches": [m.to_dict() for m in self.matches],
            "restricted_hint": self.restricted_hint.to_dict() if self.restricted_hint else None,
            "no_match_at_all": self.no_match_at_all,
        }


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _restricted_hint_for(session, book: Book, requester_id: int, requester_group_ids: set[int]) -> RestrictedHint | None:
    """Which club (if any) the requester could join to see this book —
    reveals only the club name, never the book or its owner."""
    owner_memberships = session.scalars(
        select(GroupMembership).where(GroupMembership.user_id == book.owner_id)
    ).all()
    for membership in owner_memberships:
        if membership.group_id not in requester_group_ids:
            return RestrictedHint(club_name=membership.group.name)
    return None


def ask_librarian(query: str, requester_id: int) -> LibrarianResult:
    """The core "Ask the Librarian" search. Never raises for a "no
    match" outcome — that's a valid result, not an error. Network/API
    failures still propagate as their own natural exception.
    """
    query_vector = embed_text(query, task_type="RETRIEVAL_QUERY")
    visible_owner_ids = get_visible_owner_ids(requester_id)

    with get_session() as session:
        all_embedded_books = session.scalars(
            select(Book).where(Book.embedding.is_not(None))
        ).all()

        scored = []
        for book in all_embedded_books:
            vector = json.loads(book.embedding)
            score = _cosine_similarity(query_vector, vector)
            scored.append((score, book))
        scored.sort(key=lambda pair: pair[0], reverse=True)

        visible_good_matches = [
            (score, book) for score, book in scored
            if score >= MATCH_THRESHOLD and book.owner_id in visible_owner_ids
        ]
        if visible_good_matches:
            matches = [
                LibrarianMatch(book_id=b.id, title=b.title, author=b.author, similarity=score)
                for score, b in visible_good_matches[:5]
            ]
            return LibrarianResult(matches=matches, restricted_hint=None, no_match_at_all=False)

        hidden_good_matches = [
            (score, book) for score, book in scored
            if score >= MATCH_THRESHOLD and book.owner_id not in visible_owner_ids
        ]
        if hidden_good_matches:
            requester_group_ids = {
                m.group_id
                for m in session.scalars(
                    select(GroupMembership).where(GroupMembership.user_id == requester_id)
                ).all()
            }
            best_score, best_book = hidden_good_matches[0]
            hint = _restricted_hint_for(session, best_book, requester_id, requester_group_ids)
            return LibrarianResult(matches=[], restricted_hint=hint, no_match_at_all=False)

        return LibrarianResult(matches=[], restricted_hint=None, no_match_at_all=True)


__all__ = ["LibrarianMatch", "RestrictedHint", "LibrarianResult", "ask_librarian", "MATCH_THRESHOLD"]