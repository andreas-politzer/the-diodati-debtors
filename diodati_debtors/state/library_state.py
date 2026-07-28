"""Library state — browsing books: Personal/Common Library with
search, genre/availability filters, and sorting, plus the shared user
list and lendable-book options used elsewhere.

Split out of the former monolithic LibraryState (see Struktur.md,
"LibraryState aufteilen" backlog entry) — this class now owns exactly
one responsibility: "what books can I see right now, and how are they
arranged?" Detail/edit/delete, member libraries, and loan activity
live in their own State classes (BookDetailState, MemberLibraryState,
LoanActivityState).
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import book_service, loan_service, user_service
from .auth_state import AuthState
from .group_state import GroupState


@dataclass
class BookView:
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


class LibraryState(rx.State):
    active_tab: str = "personal"  # "personal" | "common"

    books: list[BookView] = []
    users: list[dict] = []
    error_message: str = ""
    info_message: str = ""

    library_search_query: str = ""
    genre_filter: str = "All"
    availability_filter: str = "All"
    sort_option: str = "Recently added"

    lendable_book_options: list[str] = []

    def set_tab(self, tab: str):
        self.active_tab = tab
        return LibraryState.load_books

    def set_library_search_query(self, value: str):
        self.library_search_query = value
        return LibraryState.load_books

    def set_genre_filter(self, value: str):
        self.genre_filter = value
        return LibraryState.load_books

    def set_availability_filter(self, value: str):
        self.availability_filter = value
        return LibraryState.load_books

    def set_sort_option(self, value: str):
        self.sort_option = value
        return LibraryState.load_books

    def reset_book_controls(self):
        self.library_search_query = ""
        self.genre_filter = "All"
        self.availability_filter = "All"
        self.sort_option = "Recently added"
        return LibraryState.load_books

    async def _build_book_views(self, book_results) -> list[BookView]:
        auth_state = await self.get_state(AuthState)
        current_user_id = (
            int(auth_state.current_user_id) if auth_state.is_logged_in else None
        )

        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return []
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

        views: list[BookView] = []
        for book in book_results:
            active_loan = active_loans.get(book.id)
            views.append(
                BookView(
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
        return views

    def _finalize_book_list(self, views: list[BookView]) -> list[BookView]:
        if self.availability_filter == "Available only":
            views = [v for v in views if not v.is_on_loan]

        if self.sort_option == "Title (A-Z)":
            views = sorted(views, key=lambda b: b.title.lower())
        elif self.sort_option == "Author (A-Z)":
            views = sorted(views, key=lambda b: (b.author or "").split()[-1].lower() if b.author else "")
        elif self.sort_option == "Location":
            views = sorted(views, key=lambda b: (b.location or "").lower())
        elif self.sort_option == "Availability":
            views = sorted(views, key=lambda b: b.is_on_loan)
        elif self.sort_option == "Recently added":
            views = list(reversed(views))

        return views

    async def load_books(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        search = self.library_search_query or None
        genre = None if self.genre_filter in ("", "All") else self.genre_filter

        try:
            if self.active_tab == "personal":
                if not auth_state.is_logged_in:
                    self.books = []
                    return
                book_results = book_service.list_books_for_owner(
                    int(auth_state.current_user_id), search=search, genre=genre
                )
            else:
                group_state = await self.get_state(GroupState)
                if not group_state.current_group_id:
                    self.books = []
                    return
                book_results = book_service.list_books_for_group(
                    int(group_state.current_group_id), search=search, genre=genre
                )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        views = await self._build_book_views(book_results)
        self.books = self._finalize_book_list(views)

    def load_users(self):
        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.users = [u.to_dict() for u in user_results]

    async def load_all(self):
        await self.load_books()
        self.load_users()

    async def load_lendable_book_options(self):
        """Own books currently available (no active loan) — feeds the
        book picker on the Lend-to-Contact page.
        """
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.lendable_book_options = []
            return
        try:
            books = book_service.list_books_for_owner(int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return

        book_ids = [b.id for b in books]
        active_loans = loan_service.get_active_loans_for_books(book_ids)
        self.lendable_book_options = [
            f"{b.id}: {b.title}" for b in books if b.id not in active_loans
        ]


__all__ = ["LibraryState", "BookView"]