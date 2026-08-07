"""Book Detail state — the adapter for viewing/editing a single book:
detail view, the shared Add/Edit form, ISBN lookup, Open Library title
search, the Synopsis pipeline (manual/Open Library/AI), and deletion.

Split out of the former monolithic LibraryState (see Struktur.md,
"LibraryState aufteilen" backlog entry) — same architecture contract
applies: State is orchestration, not business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import book_service, contact_service, loan_service, user_service
from .auth_state import AuthState


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
    borrowing_visibility: str = "club_only"
    owner_name: str = ""
    status: str = ""
    owner_id: int = 0
    is_own_book: bool = False
    summary: str | None = None
    summary_source: str | None = None


@dataclass
class BookSearchResultView:
    work_key: str
    title: str
    author: str | None = None
    publish_year: int | None = None
    edition_count: int | None = None
    isbn: str | None = None
    cover_url: str | None = None


class BookDetailState(rx.State):
    detail_book: BookDetailView | None = None
    loan_history: list[LoanHistoryEntry] = []
    error_message: str = ""
    info_message: str = ""
    pending_delete_book_id: int = 0  # 0 == nothing pending
    pending_clear_summary: bool = False

    form_title: str = ""
    form_author: str = ""
    form_isbn: str = ""
    form_location: str = ""
    form_genre: str = ""
    form_borrowing_visibility: str = ""
    form_summary: str = ""

    search_query: str = ""
    search_results: list[BookSearchResultView] = []

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

    def set_form_borrowing_visibility(self, value: str):
        self.form_borrowing_visibility = value

    def set_form_summary(self, value: str):
        self.form_summary = value

    def confirm_clear_summary(self):
        self.pending_clear_summary = True

    def cancel_clear_summary(self):
        self.pending_clear_summary = False

    async def load_book_detail(self):
        self.error_message = ""
        self.detail_book = None
        self.loan_history = []
        try:
            bid = int(self.book_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid book id."
            return

        auth_state = await self.get_state(AuthState)
        current_user_id = (
            int(auth_state.current_user_id) if auth_state.is_logged_in else None
        )

        if current_user_id is None:
            self.error_message = "You must be logged in to view this book."
            return
        try:
            book = book_service.get_book(current_user_id, bid)
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
            borrowing_visibility=book.borrowing_visibility,
            owner_name=owner.display_name,
            status="on loan" if active_loan else "available",
            owner_id=book.owner_id,
            is_own_book=(book.owner_id == current_user_id),
            summary=book.summary,
            summary_source=book.summary_source,
        )

        history: list[LoanHistoryEntry] = []
        for loan in loans:
            if loan.contact_id is not None:
                try:
                    borrower_name = f"{contact_service.get_contact(loan.contact_id).name} (contact)"
                except DiodatiError:
                    borrower_name = "Unknown contact"
            else:
                try:
                    borrower_name = user_service.get_user(loan.borrower_id).display_name
                except DiodatiError:
                    borrower_name = "Unknown"
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

    def _populate_form_from_detail(self):
        if self.detail_book is None:
            return
        self.form_title = self.detail_book.title
        self.form_author = self.detail_book.author or ""
        self.form_isbn = self.detail_book.isbn or ""
        self.form_location = self.detail_book.location or ""
        self.form_genre = self.detail_book.genre or ""
        self.form_borrowing_visibility = self.detail_book.borrowing_visibility
        self.form_summary = (
            self.detail_book.summary
            if self.detail_book.summary_source == "owner"
            else ""
        )

    def reset_form_fields(self):
        """Called on entering Add Book fresh — clears any stale values
        left over from a previous edit session.
        """
        self.form_title = ""
        self.form_author = ""
        self.form_isbn = ""
        self.form_location = ""

    def fetch_isbn_metadata(self):
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
        except Exception:
            self.error_message = (
                "Open Library seems to be unavailable right now. "
                "You can still fill in the details manually, or try again shortly."
            )
            return
        self.form_title = metadata.title
        if metadata.author:
            self.form_author = metadata.author
        self.info_message = "Filled in from Open Library — check before saving."

    def set_search_query(self, value: str):
        self.search_query = value

    def run_search(self):
        self.error_message = ""
        self.info_message = ""
        try:
            results = book_service.search_books(self.search_query)
        except DiodatiError as e:
            self.error_message = str(e)
            self.search_results = []
            return
        except Exception:
            self.error_message = (
                "Open Library seems to be unavailable right now. "
                "Please try again shortly."
            )
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

    async def submit_summary_manual(self, form_data: dict):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            book_service.set_summary(
                int(self.book_id),
                owner_id=int(auth_state.current_user_id),
                summary=form_data.get("summary", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Summary saved."
            await self.load_book_detail()

    async def fetch_summary_open_library(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            book_service.fetch_summary_from_open_library(
                int(self.book_id), owner_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Summary fetched from Open Library."
            await self.load_book_detail()

    async def generate_summary_ai(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            book_service.generate_summary_with_ai(
                int(self.book_id), owner_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Summary generated."
            await self.load_book_detail()

    async def clear_summary(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            book_service.clear_summary(
                int(self.book_id), owner_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Summary cleared."
            self.pending_clear_summary = False
            await self.load_book_detail()

    async def submit_book_form(self, form_data: dict):
        """Handles both Add Book and Edit Book — if form_data contains
        a non-empty book_id, updates that book; otherwise creates a
        new one. Redirects on success: create → Dashboard, edit → the
        book's Detail page.
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
                    borrowing_visibility=form_data.get("borrowing_visibility") or None,
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
                    borrowing_visibility=form_data.get("borrowing_visibility") or None,
                )
                self.info_message = "Book added."
        except DiodatiError as e:
            self.error_message = str(e)
            return

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
        return rx.redirect("/dashboard")


__all__ = ["BookDetailState", "BookDetailView", "LoanHistoryEntry", "BookSearchResultView"]