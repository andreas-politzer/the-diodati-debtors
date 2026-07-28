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
import logging

logger = logging.getLogger(__name__)
from dataclasses import asdict, dataclass

from sqlalchemy import select

from .external.gemini_client import embed_text
from .external import google_books_client
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
        f"CRITICAL RULES FOR METADATA ACCURACY:\n"
        f"1. You must strictly respect the exact title and author of the "
        f"provided matches.\n"
        f"2. Do NOT invent formats or adaptations. If the user asked for a "
        f"specific format (e.g., 'graphic novel', 'manga', 'audiobook', "
        f"'movie') or a specific adaptation, and the provided matches are "
        f"clearly just the standard original novels, you must NOT pretend "
        f"the matches are the requested format.\n"
        f"3. Instead, politely and wittily correct the user. Acknowledge "
        f"what they asked for, but clearly state that the Diodati vaults "
        f"currently only hold the original, standard text editions of "
        f"these works.\n\n"
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
    """Architecture (per ChatGPT's review, 28.07): a catalogue verifies
    books, it does not answer knowledge questions. Gemini first
    classifies the query — direct search/recommendation vs. a
    knowledge question about books — via structured JSON, not a magic
    string. Knowledge-question candidates are individually verified
    against Google Books; unverifiable ones are silently dropped, never
    shown. Direct searches go straight to Google Books with the user's
    own words. Either way, Gemini never presents a book that Google
    Books hasn't confirmed exists — including in its free-text remark,
    which is explicitly forbidden from naming any book when none were
    verified (28.07 fix: Byron was naming books in prose even when the
    structured books list was empty).
    """
    logger.info("External: requesting classification from Gemini...")
    classification_prompt = (
        f'Someone asked a librarian: "{query}"\n\n'
        f"Decide whether this is (a) a direct search or recommendation "
        f'request (e.g. "books like Dracula", "gothic horror recommendations", '
        f'"Thomas Mann novels") — a catalogue can search for this directly — '
        f"or (b) a knowledge question about books "
        f'(e.g. "are there graphic novel adaptations of X", "which novels '
        f'were adapted into manga", "did author Y write genre Z") — a '
        f"catalogue cannot answer this, only knowledge can.\n\n"
        f"Reply with ONLY a JSON object, nothing else, in exactly this shape:\n\n"
        f'For direct search: {{"query_type": "direct_search"}}\n\n'
        f'For knowledge questions: {{"query_type": "knowledge", '
        f'"answer": "a short, direct answer to the question in 1-2 '
        f'sentences", "candidate_books": [{{"title": "...", "author": "..."}}]}} '
        f"— list up to 3 real books you are aware of that support your "
        f"answer. If you are not confident any real book exists, return an "
        f"empty candidate_books list rather than guessing, but still give "
        f"your best honest answer."
    )

    try:
        raw = generate_text(classification_prompt)
        logger.info("External: classification received: %r", raw[:300])
        classification = json.loads(_strip_json_fence(raw))
    except Exception:
        logger.exception("External: classification call/parse failed, defaulting to direct_search")
        classification = {"query_type": "direct_search"}

    query_type = classification.get("query_type", "direct_search")
    knowledge_answer = None
    logger.info("External: query_type=%s", query_type)

    if query_type == "knowledge":
        knowledge_answer = (classification.get("answer") or "").strip() or None
        books = []
        candidates_to_check = classification.get("candidate_books", [])[:3]
        logger.info("External: %d candidate books to verify: %r", len(candidates_to_check), candidates_to_check)
        for i, candidate in enumerate(candidates_to_check):
            title = (candidate.get("title") or "").strip()
            author = (candidate.get("author") or "").strip() or None
            if not title:
                continue
            logger.info("External: candidate %d/%d searching Google Books for %r by %r", i + 1, len(candidates_to_check), title, author)
            try:
                results = google_books_client.search_books(
                    f"{title} {author or ''}".strip(), max_results=3
                )
            except Exception:
                logger.exception("External: Google Books search failed for candidate %r", title)
                results = []

            verified_book = None
            for res in results:
                if title.lower() in res.title.lower() or res.title.lower() in title.lower():
                    verified_book = res
                    break

            logger.info(
                "External: candidate %d/%d done, raw_results=%d, verified=%s",
                i + 1, len(candidates_to_check), len(results), bool(verified_book)
            )

            if verified_book:
                books.append(
                    ExternalBook(
                        title=verified_book.title, author=verified_book.author,
                        cover_url=verified_book.cover_url, isbn=verified_book.isbn, work_key=None,
                    )
                )
        if not knowledge_answer and not books:
            logger.info("External: no answer and no verified books, returning None")
            return None
    else:
        logger.info("External: direct_search — searching Google Books with original query %r", query)
        try:
            candidates = google_books_client.search_books(query, max_results=5)
        except Exception:
            logger.exception("External: Google Books direct search failed")
            candidates = []
        logger.info("External: direct search returned %d candidates", len(candidates))
        if not candidates:
            return None
        books = [
            ExternalBook(
                title=c.title, author=c.author,
                cover_url=c.cover_url, isbn=c.isbn, work_key=None,
            )
            for c in candidates[:3]
        ]

    titles_list = ", ".join(b.title for b in books) if books else ""

    if titles_list:
        context_block = f"Real books found in the catalogue that support/illustrate this: {titles_list}.\n\n"
        forbidden_block = ""
    else:
        context_block = "No specific supporting books were found in the catalogue.\n\n"
        forbidden_block = (
            "CRITICAL: No specific books were found or verified for this "
            "query. Do NOT name, mention, or imply any specific book title "
            "in your response, even ones you might personally know of — "
            "only speak in general terms about the topic itself.\n\n"
        )

    if knowledge_answer:
        answer_block = f"Here is the factual answer to their question: {knowledge_answer}\n\n"
    else:
        answer_block = ""

    logger.info("External: requesting Byron remark from Gemini...")
    remark_prompt = (
        f"You are Lord Byron, speaking as a witty, slightly arrogant but "
        f'charming 19th-century English gentleman librarian. Someone asked: '
        f'"{query}".\n\n'
        f"{answer_block}"
        f"{context_block}"
        f"{forbidden_block}"
        f"Write ONE short remark (2-4 sentences total), in character, "
        f"dandyish and a touch superior but ultimately warm and "
        f"enthusiastic, addressing the person informally in period style. "
        f"Convey the actual answer to their question, not just a list of "
        f"book titles — the books are supporting evidence, not the whole "
        f"reply. Do not mention any book other than the ones listed above.\n\n"
        f"IMPORTANT: If the subject matter is serious, tragic, painful, "
        f"or historically grave (war, genocide, atrocity, death, "
        f"suffering, or similar), let your usual wit soften into genuine "
        f"respect and gravity. Never joke about real historical tragedy "
        f"or human suffering, even lightly. Your voice may remain "
        f"present, but reverence comes first."
    )
    try:
        remark = generate_text(remark_prompt).strip()
        logger.info("External: Byron remark received")
    except Exception:
        logger.exception("External: Byron remark call failed")
        remark = (
            knowledge_answer
            or (f"I daresay you shall find {titles_list} most diverting." if titles_list else "The librarian ponders in silence.")
        )

    return ExternalRecommendation(books=books, remark=remark)


def _strip_json_fence(raw: str) -> str:
    """Gemini sometimes wraps JSON in a markdown code fence
    (```json ... ```) despite being asked not to — strip it
    defensively before parsing."""
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```")[1]
        if stripped.startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()

__all__ = [
    "LibrarianMatch", "RestrictedHint", "LibrarianResult",
    "ExternalBook", "ExternalRecommendation",
    "ask_librarian", "get_external_recommendation", "MATCH_THRESHOLD", "get_match_remark",
]