"""Librarian state — the adapter between Reflex UI and
librarian_service. Separate bounded context, own state class, per the
project's established discipline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import librarian_service
from .auth_state import AuthState


@dataclass
class MatchView:
    book_id: int
    title: str
    author: str | None
    similarity: float


@dataclass
class ExternalBookView:
    title: str
    author: str = ""
    cover_url: str = ""
    work_key: str = ""


class LibrarianState(rx.State):
    query: str = ""
    has_searched: bool = False
    matches: list[MatchView] = []
    restricted_club_name: str = ""

    external_books: list[ExternalBookView] = []
    external_remark: str = ""

    error_message: str = ""

    def set_query(self, value: str):
        self.query = value

    async def ask(self):
        self.error_message = ""
        self.has_searched = True
        self.matches = []
        self.restricted_club_name = ""
        self.external_books = []
        self.external_remark = ""

        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to ask the librarian."
            return
        if not self.query.strip():
            self.error_message = "Tell the librarian what you're looking for."
            return

        try:
            result = librarian_service.ask_librarian(
                self.query, int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        except Exception:
            self.error_message = (
                "The librarian is momentarily unavailable. Please try again."
            )
            return

        if result.matches:
            self.matches = [
                MatchView(book_id=m.book_id, title=m.title, author=m.author, similarity=m.similarity)
                for m in result.matches
            ]
            try:
                self.external_remark = librarian_service.get_match_remark(self.query, result.matches)
            except Exception:
                self.external_remark = ""
            return

        # No visible match — a restricted hint and an external
        # recommendation are not mutually exclusive (Andy's correction:
        # "the librarian knows all books").
        if result.restricted_hint:
            self.restricted_club_name = result.restricted_hint.club_name

        try:
            recommendation = librarian_service.get_external_recommendation(self.query)
        except Exception:
            recommendation = None

        if recommendation:
            self.external_remark = recommendation.remark
            self.external_books = [
                ExternalBookView(
                    title=b.title,
                    author=b.author or "",
                    cover_url=b.cover_url or "",
                    work_key=b.work_key or "",
                )
                for b in recommendation.books
            ]


__all__ = ["LibrarianState", "MatchView", "ExternalBookView"]