"""Librarian state — the adapter between Reflex UI and
librarian_service. Separate bounded context, own state class, per the
project's established discipline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import reflex as rx
import asyncio
import logging

logger = logging.getLogger(__name__)

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

        logger.info("Librarian: starting ask_librarian for query=%r", self.query)
        try:
            result = await asyncio.to_thread(
                librarian_service.ask_librarian, self.query, int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        except Exception:
            logger.exception("Librarian: ask_librarian failed")
            self.error_message = (
                "The librarian is momentarily unavailable. Please try again."
            )
            return
        logger.info("Librarian: ask_librarian finished, matches=%d", len(result.matches))

        if result.matches:
            self.matches = [
                MatchView(book_id=m.book_id, title=m.title, author=m.author, similarity=m.similarity)
                for m in result.matches
            ]
            logger.info("Librarian: starting get_match_remark")
            try:
                self.external_remark = await asyncio.to_thread(
                    librarian_service.get_match_remark, self.query, result.matches
                )
            except Exception:
                logger.exception("Librarian: get_match_remark failed")
                self.external_remark = ""
            logger.info("Librarian: get_match_remark finished")
            return

        if result.restricted_hint:
            self.restricted_club_name = result.restricted_hint.club_name

        logger.info("Librarian: starting get_external_recommendation")
        try:
            recommendation = await asyncio.to_thread(
                librarian_service.get_external_recommendation, self.query
            )
        except Exception:
            logger.exception("Librarian: get_external_recommendation failed")
            recommendation = None
        logger.info("Librarian: get_external_recommendation finished, found=%s", recommendation is not None)

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