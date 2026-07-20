"""Library state — the adapter between Reflex UI and the service layer.

Per the Architecture Contract: State is orchestration, not business
logic. Service decides whether an action is allowed; State decides
when to call the service and translates results/errors into UI-facing
state; UI only renders state and triggers events.

BookView is a typed dataclass, not a plain dict — Reflex needs
explicit field types to compile rx.foreach over a nested list
(borrower_options) correctly; an untyped list[dict] leaves every value
as `Any`, which breaks exactly that case (rediscovered the hard way —
see Roadmap.md lesson learned).

Tab state (Common/Personal) is a genuine UI concern: the data source
changes, the presentation stays identical — one shared book list
rendering, fed by different service calls depending on active_tab.
Default tab is "personal" (works with zero clubs, per Domain Model v2
principle 1), not "common".
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
    is_on_loan: bool = False
    status: str = ""
    active_loan_id: int | None = None
    borrower_id: int | None = None
    borrower_options: list[str] = field(default_factory=list)


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
    users: list[dict] = []
    user_options: list[str] = []
    detail_book: BookDetailView | None = None
    loan_history: list[LoanHistoryEntry] = []
    error_message: str = ""

    def set_tab(self, tab: str):
        self.active_tab = tab
        return LibraryState.load_books

    async def load_books(self):
        """Fetch books for the active tab plus loan status, in two
        service calls total (not one per book — see
        get_active_loans_for_books).
        """
        self.error_message = ""
        auth_state = await self.get_state(AuthState)

        try:
            user_results = user_service.list_users()

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

        book_ids = [b.id for b in book_results]
        active_loans = loan_service.get_active_loans_for_books(book_ids)

        enriched: list[BookView] = []
        for book in book_results:
            active_loan = active_loans.get(book.id)
            borrower_options = [
                f"{u.id}: {u.display_name}"
                for u in user_results
                if u.id != book.owner_id
            ]
            enriched.append(
                BookView(
                    id=book.id,
                    owner_id=book.owner_id,
                    title=book.title,
                    author=book.author,
                    isbn=book.isbn,
                    location=book.location,
                    is_on_loan=active_loan is not None,
                    status="on loan" if active_loan else "available",
                    active_loan_id=active_loan.id if active_loan else None,
                    borrower_id=active_loan.borrower_id if active_loan else None,
                    borrower_options=borrower_options,
                )
            )
        self.books = enriched

    def load_users(self):
        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.users = [u.to_dict() for u in user_results]
        self.user_options = [f"{u.id}: {u.display_name}" for u in user_results]

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

    async def lend_book(self, book_id: int, selected_user_option: str, due_in_days: int = 14):
        self.error_message = ""
        if not selected_user_option:
            self.error_message = "Select a borrower first."
            return
        try:
            borrower_id = int(selected_user_option.split(":", 1)[0].strip())
        except (ValueError, IndexError):
            self.error_message = "Invalid borrower selection."
            return
        try:
            loan_service.create_loan(
                book_id=int(book_id),
                borrower_id=borrower_id,
                due_date=dt.date.today() + dt.timedelta(days=due_in_days),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_books()

    async def return_book(self, loan_id: int | None):
        self.error_message = ""
        if loan_id is None:
            self.error_message = "No active loan to return."
            return
        try:
            loan_service.return_loan(int(loan_id))
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_books()

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