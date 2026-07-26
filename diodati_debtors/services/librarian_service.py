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
from .external.gemini_client import embed_text, generate_text
from .book_service import search_books

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

    def to_dict(self) -> dict:
        return {
            "matches": [m.to_dict() for m in self.matches],
            "restricted_hint": self.restricted_hint.to_dict() if self.restricted_hint else None,
        }

@dataclass(frozen=True)
class ExternalRecommendation:
    """Up to three books Gemini suggests that aren't in the library at
    all, with real cover/metadata enrichment via Open Library where
    possible, plus a single, shared remark in Lord Byron's voice
    covering all of them together — more natural than a mechanical
    one-liner per book."""

    books: list[ExternalBook]
    remark: str

    def to_dict(self) -> dict:
        return {"books": [b.to_dict() for b in self.books], "remark": self.remark}
    
@dataclass(frozen=True)
class ExternalBook:
    title: str
    author: str | None
    cover_url: str | None
    isbn: str | None
    work_key: str | None

    def to_dict(self) -> dict:
        return asdict(self)

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

def _direct_title_matches(session, query: str, visible_owner_ids: set[int]) -> list[Book]:
    """Exact (case-insensitive) title containment — catches direct
    "do you have X?" questions that pure semantic similarity can
    under-score, since embeddings are built from a book's synopsis
    text, not from its title. No typo tolerance — that would need
    fuzzy matching, a separate, bigger addition."""
    query_lower = query.lower()
    visible_books = session.scalars(
        select(Book).where(Book.owner_id.in_(visible_owner_ids))
    ).all()
    return [b for b in visible_books if b.title and b.title.lower() in query_lower]


def ask_librarian(query: str, requester_id: int) -> LibrarianResult:
    """The core "Ask the Librarian" search. Never raises for a "no
    match" outcome — that's a valid result, not an error. Network/API
    failures still propagate as their own natural exception.
    """
   
    visible_owner_ids = get_visible_owner_ids(requester_id)

    with get_session() as session:
        direct_matches = _direct_title_matches(session, query, visible_owner_ids)
        if direct_matches:
            matches = [
                LibrarianMatch(book_id=b.id, title=b.title, author=b.author, similarity=1.0)
                for b in direct_matches[:5]
            ]
            return LibrarianResult(matches=matches, restricted_hint=None)

        query_vector = embed_text(query, task_type="RETRIEVAL_QUERY")

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
            return LibrarianResult(matches=matches, restricted_hint=None)

        hidden_good_matches = [
            (score, book) for score, book in scored
            if score >= MATCH_THRESHOLD and book.owner_id not in visible_owner_ids
        ]
        hint = None
        if hidden_good_matches:
            requester_group_ids = {
                m.group_id
                for m in session.scalars(
                    select(GroupMembership).where(GroupMembership.user_id == requester_id)
                ).all()
            }
            _, best_book = hidden_good_matches[0]
            hint = _restricted_hint_for(session, best_book, requester_id, requester_group_ids)

        return LibrarianResult(matches=[], restricted_hint=hint)
    
def get_match_remark(query: str, matches: list[LibrarianMatch]) -> str:
    """A short remark in Lord Byron's voice about matches found in the
    user's own visible library — the same personality as the external
    fallback, so the librarian is never a silent, personality-free
    card when he *does* find something at home.
    """
    titles_list = ", ".join(m.title for m in matches)
    prompt = (
        f"You are Lord Byron, speaking as a witty, slightly arrogant but "
        f'charming 19th-century English gentleman librarian. Someone asked '
        f'for a book matching: "{query}". You found these book(s) already '
        f"within the community's own collection — The Diodati Debtors "
        f"themselves have it. Write ONE short remark (2-4 sentences "
        f"total), in character, dandyish and a touch superior but "
        f"ultimately warm and enthusiastic, addressing the person "
        f"informally in period style. Express a sense of triumphant "
        f"discovery that the book is right here, within the community's "
        f"own holdings — you may playfully reference \"the Diodati "
        f"debtors\" themselves as having it.\n\n"
        f"IMPORTANT: If the subject matter is serious, tragic, painful, "
        f"or historically grave (war, genocide, atrocity, death, "
        f"suffering, or similar), let your usual wit soften into genuine "
        f"respect and gravity. Never joke about real historical tragedy "
        f"or human suffering, even lightly. Your voice may remain "
        f"present, but reverence comes first."
    )
    try:
        return generate_text(prompt).strip()
    except Exception:
        return f"Ah, I believe you'll find {titles_list} quite to your taste."

def get_external_recommendation(query: str) -> ExternalRecommendation | None:
    """Called whenever no visible match exists — independent of
    whether a restricted_hint also exists, per Andy's design decision:
    "the librarian knows all books", so a club hint and a suggestion
    from the wider world are not mutually exclusive.
    """
    list_prompt = (
        f"Someone is looking for a book matching this description: "
        f'"{query}". Suggest up to three real, existing books that '
        f"match, ranked best first. Reply with one book per line, "
        f"nothing else, in exactly this format:\nTitle | Author"
    )
    try:
        raw = generate_text(list_prompt)
    except Exception:
        return None

    parsed: list[tuple[str, str | None]] = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        title_part, _, author_part = line.partition("|")
        title = title_part.strip()
        author = author_part.strip() or None
        if title:
            parsed.append((title, author))

    if not parsed:
        return None

    books: list[ExternalBook] = []
    for title, author in parsed[:3]:
        try:
            search_results = search_books(f"{title} {author or ''}".strip())
        except Exception:
            search_results = []

        cover_url = None
        isbn = None
        work_key = None
        if search_results:
            best = search_results[0]
            title = best.title
            author = best.author
            isbn = best.isbn
            work_key = best.work_key
            if best.cover_id:
                cover_url = f"https://covers.openlibrary.org/b/id/{best.cover_id}-M.jpg"

        books.append(
            ExternalBook(title=title, author=author, cover_url=cover_url, isbn=isbn, work_key=work_key)
        )

    titles_list = ", ".join(b.title for b in books)
    remark_prompt = (
        f"You are Lord Byron, speaking as a witty, slightly arrogant but "
        f'charming 19th-century English gentleman librarian. Someone asked '
        f'for a book matching: "{query}". You want to recommend these '
        f"book(s): {titles_list}. Write ONE short remark (2-4 sentences "
        f"total), in character, dandyish and a touch superior but "
        f"ultimately warm and enthusiastic, addressing the person "
        f"informally in period style. Mention the book(s) naturally.\n\n"
        f"IMPORTANT: If the subject matter is serious, tragic, painful, "
        f"or historically grave (war, genocide, atrocity, death, "
        f"suffering, or similar), let your usual wit soften into genuine "
        f"respect and gravity. Never joke about real historical tragedy "
        f"or human suffering, even lightly. Your voice may remain "
        f"present, but reverence comes first."
    )
    try:
        remark = generate_text(remark_prompt).strip()
    except Exception:
        remark = f"I daresay you shall find {titles_list} most diverting."

    return ExternalRecommendation(books=books, remark=remark)

__all__ = [
    "LibrarianMatch", "RestrictedHint", "LibrarianResult",
    "ExternalBook", "ExternalRecommendation",
    "ask_librarian", "get_external_recommendation", "MATCH_THRESHOLD", "get_match_remark",
]