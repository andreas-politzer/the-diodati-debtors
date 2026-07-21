"""Library state — the adapter between Reflex UI and the service layer.

Per the Architecture Contract: State is orchestration, not business
logic. Service decides whether an action is allowed; State decides
when to call the service and translates results/errors into UI-facing
state; UI only renders state and triggers events.

submit_book_form() unifies create/edit: if the submitted book_id is
present, it updates; otherwise it creates. One shared BookForm
component (ui/components/book_form.py) drives both modes, per Codex's
review — no duplicated Add/Edit forms.

Known, accepted gap: edit/delete are hidden from non-owners in the UI
(book_action_bar only shows them when is_own_book), but the edit page
itself has no additional server-side page guard beyond what
book_service already enforces (NotAuthorizedError on submit). A
non-owner typing the URL directly would see the form but get an error
on submit, not be redirected away. Acceptable for this project's scale.
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
    genre: str | None = None
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
    genre: str | None = None
    owner_name: str = ""
    status: str = ""

@dataclass
class BorrowedLoanView:
    id: int
    book_id: int
    book_title: str
    owner_name: str
    loan_date: str
    due_date: str
    return_date: str | None = None
    is_active: bool = False
    is_overdue: bool = False
    is_due_soon: bool = False  # due within 3 days, not yet overdue

@dataclass
class BookSearchResultView:
    work_key: str
    title: str
    author: str | None = None
    publish_year: int | None = None
    edition_count: int | None = None
    isbn: str | None = None
    cover_url: str | None = None


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
    pending_delete_book_id: int = 0  # 0 == nothing pending
    form_title: str = ""
    form_author: str = ""
    form_isbn: str = ""
    form_location: str = ""
    form_genre: str = ""
    search_query: str = ""
    search_results: list[BookSearchResultView] = []
    borrowed_loans: list[BorrowedLoanView] = []

    def set_form_title(self, value: str):
        self.form_title = value

    def set_form_author(self, value: str):
        self.form_author = value

    def set_form_isbn(self, value: str):
        self.form_isbn = value

    def set_form_location(self, value: str):
        self.form_location = value

    def set_form_genre(self, value: str):
        self.form_genre = value

    def set_tab(self, tab: str):
        self.active_tab = tab
        if tab == "borrowed":
            return LibraryState.load_borrowed_books
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

    async def load_books(self):
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
            genre=book.genre,
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
        self._populate_form_from_detail()

    async def load_borrowed_books(self):
        """Populate 'My Borrowed Books' — active loans (with overdue/
        due-soon status) and full borrow history, split in the UI by
        is_active, not by two separate queries.
        """
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.borrowed_loans = []
            return

        try:
            loans = loan_service.list_loans_for_borrower(
                int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        today = dt.date.today()
        views: list[BorrowedLoanView] = []
        for loan in loans:
            try:
                book = book_service.get_book(loan.book_id)
                owner = user_service.get_user(book.owner_id)
                book_title = book.title
                owner_name = owner.display_name
            except DiodatiError:
                book_title = f"Book {loan.book_id}"
                owner_name = "Unknown"

            is_overdue = loan.is_active and loan.due_date < today
            is_due_soon = (
                loan.is_active
                and not is_overdue
                and (loan.due_date - today).days <= 3
            )

            views.append(
                BorrowedLoanView(
                    id=loan.id,
                    book_id=loan.book_id,
                    book_title=book_title,
                    owner_name=owner_name,
                    loan_date=loan.loan_date.isoformat(),
                    due_date=loan.due_date.isoformat(),
                    return_date=loan.return_date.isoformat() if loan.return_date else None,
                    is_active=loan.is_active,
                    is_overdue=is_overdue,
                    is_due_soon=is_due_soon,
                )
            )
        self.borrowed_loans = views

    def reset_form_fields(self):
        """Called on entering Add Book fresh — clears any stale values
        left over from a previous edit session.
        """
        self.form_title = ""
        self.form_author = ""
        self.form_isbn = ""
        self.form_location = ""

    def _populate_form_from_detail(self):
        """Called after load_book_detail() in edit mode, so the
        controlled inputs show the book's current values.
        """
        if self.detail_book is None:
            return
        self.form_title = self.detail_book.title
        self.form_author = self.detail_book.author or ""
        self.form_isbn = self.detail_book.isbn or ""
        self.form_location = self.detail_book.location or ""
        self.form_genre = self.detail_book.genre or ""

    def fetch_isbn_metadata(self):
        """Look up the ISBN currently in form_isbn and prefill
        title/author on success. Does not touch form_location — the
        user's own note (e.g. shelf location) isn't something Open
        Library would know anyway.
        """
        self.error_message = ""
        self.info_message = ""
        if not self.form_isbn.strip():
            self.error_message = "Enter an ISBN first."
            return
        try:
            metadata = book_service.lookup_isbn(self.form_isbn)
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.form_title = metadata.title
        if metadata.author:
            self.form_author = metadata.author
        self.info_message = "Filled in from Open Library — check before saving."


    def set_search_query(self, value: str):
        self.search_query = value

    def run_search(self):
        """Title search — a completely separate workflow from ISBN
        lookup. Presents candidates with cover art; never auto-selects
        one. The user always makes the final choice.
        """
        self.error_message = ""
        self.info_message = ""
        try:
            results = book_service.search_books(self.search_query)
        except DiodatiError as e:
            self.error_message = str(e)
            self.search_results = []
            return
        self.search_results = [
            BookSearchResultView(
                work_key=r.work_key,
                title=r.title,
                author=r.author,
                publish_year=r.publish_year,
                edition_count=r.edition_count,
                isbn=r.isbn,
                cover_url=(
                    f"https://covers.openlibrary.org/b/id/{r.cover_id}-M.jpg"
                    if r.cover_id
                    else None
                ),
            )
            for r in results
        ]
        if not self.search_results:
            self.info_message = "No matches found."

    def select_search_result(self, work_key: str):
        """Populate the form from the chosen candidate — same
        form_* fields as ISBN lookup and manual typing. BookForm
        itself never knows where the data came from.
        """
        match = next((r for r in self.search_results if r.work_key == work_key), None)
        if match is None:
            return
        self.form_title = match.title
        if match.author:
            self.form_author = match.author
        if match.isbn:
            self.form_isbn = match.isbn
        self.search_results = []
        self.search_query = ""
        self.info_message = "Filled in from Open Library search — check before saving."

    def clear_search(self):
        self.search_query = ""
        self.search_results = []

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

    async def submit_book_form(self, form_data: dict):
        """Handles both Add Book and Edit Book — if form_data contains
        a non-empty book_id, updates that book; otherwise creates a
        new one. One shared form, one shared handler. Redirects on
        success: create → Dashboard, edit → the book's Detail page.
        """
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return

        book_id_raw = form_data.get("book_id", "")
        try:
            if book_id_raw:
                book_service.update_book(
                    int(book_id_raw),
                    owner_id=int(auth_state.current_user_id),
                    title=form_data.get("title", ""),
                    author=form_data.get("author", ""),
                    isbn=form_data.get("isbn", ""),
                    location=form_data.get("location", ""),
                    genre=(
                        None
                        if form_data.get("genre", "") in ("", "—")
                        else form_data.get("genre")
                    ),
                )
                self.info_message = "Book updated."
            else:
                book_service.create_book(
                    owner_id=int(auth_state.current_user_id),
                    title=form_data.get("title", ""),
                    author=form_data.get("author", ""),
                    isbn=form_data.get("isbn", ""),
                    location=form_data.get("location", ""),
                    genre=(
                        None
                        if form_data.get("genre", "") in ("", "—")
                        else form_data.get("genre")
                    ),
                )
                self.info_message = "Book added."
        except DiodatiError as e:
            self.error_message = str(e)
            return

        await self.load_books()
        if book_id_raw:
            return rx.redirect(f"/book/{book_id_raw}")
        return rx.redirect("/dashboard")

    def confirm_delete(self, book_id: int):
        self.pending_delete_book_id = int(book_id)

    def cancel_delete(self):
        self.pending_delete_book_id = 0

    async def delete_book(self, book_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in."
            return
        try:
            book_service.delete_book(
                int(book_id), owner_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.pending_delete_book_id = 0
        await self.load_books()
        return rx.redirect("/dashboard")


__all__ = ["LibraryState", "BookView", "LoanHistoryEntry", "BookDetailView", "BorrowedLoanView"]