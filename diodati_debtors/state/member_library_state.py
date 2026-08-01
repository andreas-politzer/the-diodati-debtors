"""Member Library state — a read-only view into one specific member's
personal library, reusing the same book-view enrichment shape as
LibraryState (a fresh copy here, since Reflex state classes don't
share dataclasses well across modules the same way plain Python would
— see Struktur.md, "LibraryState aufteilen").
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import book_service, loan_service, trust_service, user_service
from .auth_state import AuthState
from ..services import group_service
from ..services import profile_service


@dataclass
class MemberBookView:
    id: int
    owner_id: int
    title: str
    author: str | None = None
    isbn: str | None = None
    location: str | None = None
    genre: str | None = None
    owner_name: str = ""
    is_on_loan: bool = False
    status: str = ""
    active_loan_id: int | None = None
    is_own_book: bool = False
    has_pending_request: bool = False


class MemberLibraryState(rx.State):
    member_books: list[MemberBookView] = []
    viewing_member_name: str = ""
    viewing_member_bio: str = ""
    viewing_member_profile_visible: bool = False
    viewing_member_shows_library: bool = False
    viewing_member_visibility_label: str = ""
    viewing_member_location: str = ""
    viewing_member_favorite_genre: str = ""
    viewing_member_reliability: str = ""
    viewing_member_book_care: str = ""
    error_message: str = ""

    async def load_member_library(self):
        self.error_message = ""
        self.member_books = []
        self.viewing_member_name = ""
        try:
            member_id = int(self.member_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid member id."
            return

        auth_state = await self.get_state(AuthState)
        current_user_id = (
            int(auth_state.current_user_id) if auth_state.is_logged_in else None
        )
        if current_user_id is None:
            self.error_message = "You must be logged in to view a member's library."
            return

        visible_owner_ids = group_service.get_visible_owner_ids(current_user_id)
        is_shared_club_member = member_id in visible_owner_ids

        public_profile_ids = profile_service.get_public_profile_user_ids([member_id])
        is_public_profile = member_id in public_profile_ids

        if not is_shared_club_member and not is_public_profile:
            self.error_message = "You do not have permission to view this member's profile."
            return

        self.viewing_member_shows_library = is_shared_club_member

        try:
            member = user_service.get_user(member_id)
            book_results = (
                book_service.list_books_for_owner(member_id)
                if self.viewing_member_shows_library
                else []
            )
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.viewing_member_name = member.display_name
        try:
            member_profile = profile_service.get_or_create_profile(member_id)
        except DiodatiError:
            member_profile = None

        visibility_labels = {
            "private": "Private",
            "clubs_only": "Members only",
            "public": "Public",
        }
        self.viewing_member_visibility_label = (
            visibility_labels.get(member_profile.visibility, "") if member_profile else ""
        )

        if member_profile is not None and member_profile.visibility != "private":
            self.viewing_member_profile_visible = True
            self.viewing_member_bio = member_profile.bio or ""
            self.viewing_member_location = member_profile.location or ""
            self.viewing_member_favorite_genre = member_profile.favorite_genre or ""
        else:
            self.viewing_member_profile_visible = False
            self.viewing_member_bio = ""
            self.viewing_member_location = ""
            self.viewing_member_favorite_genre = ""
        if self.viewing_member_shows_library:
            signals = trust_service.get_trust_signals(member_id)
            self.viewing_member_reliability = signals.reliability
            self.viewing_member_book_care = signals.book_care
        else:
            self.viewing_member_reliability = ""
            self.viewing_member_book_care = ""

        owner_names_by_id = {u.id: u.display_name for u in user_results}
        book_ids = [b.id for b in book_results]
        active_loans = loan_service.get_active_loans_for_books(book_ids)
        pending_request_book_ids = (
            loan_service.get_pending_request_book_ids_for_requester(
                book_ids, current_user_id
            )
            if current_user_id is not None
            else set()
        )

        views: list[MemberBookView] = []
        for book in book_results:
            active_loan = active_loans.get(book.id)
            views.append(
                MemberBookView(
                    id=book.id,
                    owner_id=book.owner_id,
                    owner_name=owner_names_by_id.get(book.owner_id, f"User {book.owner_id}"),
                    title=book.title,
                    author=book.author,
                    genre=book.genre,
                    isbn=book.isbn,
                    location=book.location,
                    is_on_loan=active_loan is not None,
                    status="on loan" if active_loan else "available",
                    active_loan_id=active_loan.id if active_loan else None,
                    is_own_book=(book.owner_id == current_user_id),
                    has_pending_request=book.id in pending_request_book_ids,
                )
            )
        self.member_books = views


__all__ = ["MemberLibraryState", "MemberBookView"]