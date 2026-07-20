"""Library state — the adapter between Reflex UI and the service layer.

Per the Architecture Contract: State is orchestration, not business
logic. Service decides whether an action is allowed; State decides
when to call the service and translates results/errors into UI-facing
state; UI only renders state and triggers events.

BookView is a typed dataclass, not a plain dict — see Struktur.md
lesson learned (rx.foreach over nested lists needs explicit typing).

Tab state (Common/Personal): the data source changes, the presentation
stays identical. Default tab is "personal" (works with zero clubs, per
Domain Model v2 principle 1).

Lending goes through the request/approval workflow
(loan_service.request_to_borrow / approve_loan_request /
decline_loan_request) instead of an instant "Lend to" picker.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

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
    owner_name: str = ""
    is_on_loan: bool = False
    status: str = ""
    active_loan_id: int | None = None
    is_own_book: bool = False
    has_pending_request: bool = False


@dataclass
class LoanHistoryEntry:
    id: int
    borrower_name: str
    loan_date: str
    due_date: str
    return_date: str | None = None
    is_active: bool = False


@dataclass
class BookDetailView:
    id: int
    title: str
    author: str | None = None
    isbn: str | None = None
    location: str | None = None
    owner_name: str = ""
    status: str = ""


class LibraryState(rx.State):
    active_tab: str = "personal"  # "personal" | "common"

    books: list[BookView] = []
    member_books: list[BookView] = []
    viewing_member_name: str = ""
    users: list[dict] = []
    detail_book: BookDetailView | None = None
    loan_history: list[LoanHistoryEntry] = []
    error_message: str = ""
    info_message: str = ""

    def set_tab(self, tab: str):
        self.active_tab = tab
        return LibraryState.load_books

    async def _build_book_views(self, book_results) -> list[BookView]:
        """Shared enrichment logic: turn plain BookResults into
        display-ready BookViews (loan status, request status,
        ownership, owner name). Used by load_books() and
        load_member_library() alike, so a member's library view and
        the dashboard's Common Library render identically — one
        rendering path, per Andy's request.
        """
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

    async def load_books(self):
        """Fetch books for the active tab (dashboard), enriched via
        _build_book_views.
        """
        self.error_message = ""
        auth_state = await self.get_state(AuthState)

        try:
            if self.active_tab == "personal":
                if not auth_state.is_logged_in:
                    self.books = []
                    return
                book_results = book_service.list_books_for_owner(
                    int(auth_state.current_user_id)
                )
            else:
                group_state = await self.get_state(GroupState)
                if not group_state.current_group_id:
                    self.books = []
                    return
                book_results = book_service.list_books_for_group(
                    int(group_state.current_group_id)
                )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.books = await self._build_book_views(book_results)

    async def load_member_library(self):
        """Populate member_books/viewing_member_name for
        /members/[member_id] — same BookView rendering as the
        dashboard, just scoped to one specific member's catalogue.
        """
        self.error_message = ""
        self.member_books = []
        self.viewing_member_name = ""
        try:
            member_id = int(self.member_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid member id."
            return

        try:
            member = user_service.get_user(member_id)
            book_results = book_service.list_books_for_owner(member_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.viewing_member_name = member.display_name
        self.member_books = await self._build_book_views(book_results)

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

    async def load_book_detail(self):
        self.error_message = ""
        self.detail_book = None
        self.loan_history = []
        try:
            bid = int(self.book_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid book id."
            return

        try:
            book = book_service.get_book(bid)
            owner = user_service.get_user(book.owner_id)
            loans = loan_service.list_loans_for_book(bid)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        active_loan = next((loan for loan in loans if loan.is_active), None)
        self.detail_book = BookDetailView(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            location=book.location,
            owner_name=owner.display_name,
            status="on loan" if active_loan else "available",
        )

        history: list[LoanHistoryEntry] = []
        for loan in loans:
            try:
                borrower_name = user_service.get_user(loan.borrower_id).display_name
            except DiodatiError:
                borrower_name = f"User {loan.borrower_id}"
            history.append(
                LoanHistoryEntry(
                    id=loan.id,
                    borrower_name=borrower_name,
                    loan_date=loan.loan_date.isoformat(),
                    due_date=loan.due_date.isoformat(),
                    return_date=loan.return_date.isoformat() if loan.return_date else None,
                    is_active=loan.is_active,
                )
            )
        self.loan_history = history

    async def request_to_borrow(self, book_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to request a book."
            return
        try:
            loan_service.request_to_borrow(
                book_id=int(book_id), requester_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Request sent — waiting for the owner's approval."
            await self.load_books()
            if self.member_id:
                await self.load_member_library()

    async def return_book(self, book: BookView):
        self.error_message = ""
        self.info_message = ""
        if not book.is_own_book:
            self.error_message = "Only the book's owner can mark it as returned."
            return
        if book.active_loan_id is None:
            self.error_message = "No active loan to return."
            return
        try:
            loan_service.return_loan(book.active_loan_id)
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_books()
            if self.member_id:
                await self.load_member_library()

    async def submit_new_book(self, form_data: dict):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to add a book."
            return
        try:
            book_service.create_book(
                owner_id=int(auth_state.current_user_id),
                title=form_data.get("title", ""),
                author=form_data.get("author", ""),
                isbn=form_data.get("isbn", ""),
                location=form_data.get("location", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_books()


__all__ = ["LibraryState", "BookView", "LoanHistoryEntry", "BookDetailView"]