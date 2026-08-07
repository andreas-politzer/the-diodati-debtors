"""Loan Activity state — borrowing and lending: My Borrowed Books
(active + history), My Lent-Out Books (active + history), requesting
to borrow, and marking a loan returned.

Split out of the former monolithic LibraryState (see Struktur.md,
"LibraryState aufteilen" backlog entry).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import book_service, contact_service, loan_service, user_service
from .auth_state import AuthState


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
    is_due_soon: bool = False


@dataclass
class LentOutLoanView:
    id: int
    book_id: int
    book_title: str
    borrower_name: str
    loan_date: str
    due_date: str
    return_date: str | None = None
    is_active: bool = False
    is_overdue: bool = False
    is_due_soon: bool = False


@dataclass
class LentOutPeriod:
    borrower_name: str
    loan_date: str
    due_date: str
    return_date: str | None = None
    is_active: bool = False


@dataclass
class LentOutHistoryGroup:
    book_id: int
    book_title: str
    periods: list[LentOutPeriod] = field(default_factory=list)


class LoanActivityState(rx.State):
    borrowed_loans: list[BorrowedLoanView] = []
    lent_out_loans: list[LentOutLoanView] = []
    lent_out_history: list[LentOutHistoryGroup] = []
    loan_sort_option: str = "Due date"
    return_condition_rating: str = ""

    request_book_id: int = 0
    request_period_choice: str = "Standard (14 days)"
    request_custom_due_date: str = ""
    request_note: str = ""

    error_message: str = ""
    info_message: str = ""

    def set_return_condition_rating(self, value: str):
        self.return_condition_rating = value

    def set_loan_sort_option(self, value: str):
        self.loan_sort_option = value
        self.borrowed_loans = self._sort_loan_views(self.borrowed_loans)
        self.lent_out_loans = self._sort_loan_views(self.lent_out_loans)

    def _sort_loan_views(self, views: list):
        if not views:
            return views
        if self.loan_sort_option == "Loan date":
            return sorted(views, key=lambda v: v.loan_date)
        if self.loan_sort_option == "Book title":
            return sorted(views, key=lambda v: v.book_title.lower())
        if self.loan_sort_option == "Person":
            name_attr = "owner_name" if hasattr(views[0], "owner_name") else "borrower_name"
            return sorted(views, key=lambda v: getattr(v, name_attr).lower())
        return sorted(views, key=lambda v: v.due_date)

    async def load_borrowed_books(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.borrowed_loans = []
            return

        user_id = int(auth_state.current_user_id)
        try:
            loans = loan_service.list_loans_for_borrower(user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        today = dt.date.today()
        views: list[BorrowedLoanView] = []
        for loan in loans:
            try:
                book = book_service.get_book(user_id, loan.book_id)
                owner = user_service.get_user(book.owner_id)
                book_title = book.title
                owner_name = owner.display_name
            except DiodatiError:
                book_title = f"Book {loan.book_id}"
                owner_name = "Unknown"

            is_overdue = loan.is_active and loan.due_date < today
            is_due_soon = loan.is_active and not is_overdue and (loan.due_date - today).days <= 3

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
        self.borrowed_loans = self._sort_loan_views(views)

    async def load_lent_out_books(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.lent_out_loans = []
            return
        user_id = int(auth_state.current_user_id)
        try:
            loans = loan_service.list_loans_for_owner(user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        today = dt.date.today()
        views: list[LentOutLoanView] = []
        for loan in loans:
            if not loan.is_active:
                continue
            try:
                book_title = book_service.get_book(user_id, loan.book_id).title
            except DiodatiError:
                book_title = f"Book {loan.book_id}"

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

            is_overdue = loan.is_active and loan.due_date < today
            is_due_soon = loan.is_active and not is_overdue and (loan.due_date - today).days <= 3

            views.append(
                LentOutLoanView(
                    id=loan.id,
                    book_id=loan.book_id,
                    book_title=book_title,
                    borrower_name=borrower_name,
                    loan_date=loan.loan_date.isoformat(),
                    due_date=loan.due_date.isoformat(),
                    return_date=loan.return_date.isoformat() if loan.return_date else None,
                    is_active=loan.is_active,
                    is_overdue=is_overdue,
                    is_due_soon=is_due_soon,
                )
            )
        self.lent_out_loans = self._sort_loan_views(views)

    async def load_lent_out_history(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.lent_out_history = []
            return
        user_id = int(auth_state.current_user_id)
        try:
            loans = loan_service.list_loans_for_owner(user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        groups_by_book: dict[int, LentOutHistoryGroup] = {}
        for loan in loans:
            if loan.is_active:
                continue
            try:
                book_title = book_service.get_book(user_id, loan.book_id).title
            except DiodatiError:
                book_title = f"Book {loan.book_id}"

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

            if loan.book_id not in groups_by_book:
                groups_by_book[loan.book_id] = LentOutHistoryGroup(
                    book_id=loan.book_id, book_title=book_title
                )
            groups_by_book[loan.book_id].periods.append(
                LentOutPeriod(
                    borrower_name=borrower_name,
                    loan_date=loan.loan_date.isoformat(),
                    due_date=loan.due_date.isoformat(),
                    return_date=loan.return_date.isoformat() if loan.return_date else None,
                    is_active=loan.is_active,
                )
            )
        self.lent_out_history = list(groups_by_book.values())

    def open_request_dialog(self, book_id: int):
        self.request_book_id = book_id
        self.request_period_choice = "Standard (14 days)"
        self.request_custom_due_date = ""
        self.request_note = ""

    def set_request_period_choice(self, value: str):
        self.request_period_choice = value

    def set_request_custom_due_date(self, value: str):
        self.request_custom_due_date = value

    def set_request_note(self, value: str):
        self.request_note = value

    async def request_to_borrow(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to request a book."
            return

        requested_due_date = None
        if self.request_period_choice == "Custom" and self.request_custom_due_date:
            try:
                requested_due_date = dt.date.fromisoformat(self.request_custom_due_date)
            except ValueError:
                self.error_message = "Invalid date."
                return

        try:
            loan_service.request_to_borrow(
                book_id=int(self.request_book_id),
                requester_id=int(auth_state.current_user_id),
                requested_due_date=requested_due_date,
                note=self.request_note or None,
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Request sent — waiting for the owner's approval."

    async def return_book(self, book) -> None:
        self.error_message = ""
        self.info_message = ""
        is_own_book = book["is_own_book"] if isinstance(book, dict) else book.is_own_book
        active_loan_id = book["active_loan_id"] if isinstance(book, dict) else book.active_loan_id

        if not is_own_book:
            self.error_message = "Only the book's owner can mark it as returned."
            return
        if active_loan_id is None:
            self.error_message = "No active loan to return."
            return

        label_to_value = {
            "Better than before": "better_than_before",
            "Same condition": "same_condition",
            "Slightly worse": "slightly_worse",
            "Significantly worse": "significantly_worse",
        }
        condition = label_to_value.get(self.return_condition_rating)

        try:
            loan_service.return_loan(active_loan_id, condition_rating=condition)
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.return_condition_rating = ""

    async def return_lent_out_book(self, loan_id: int):
        """Simpler than return_book() — here we already know the
        exact Loan ID directly (LentOutLoanView.id), no need to go
        through the generic book-object duck-typing path.
        """
        self.error_message = ""
        self.info_message = ""

        label_to_value = {
            "Better than before": "better_than_before",
            "Same condition": "same_condition",
            "Slightly worse": "slightly_worse",
            "Significantly worse": "significantly_worse",
        }
        condition = label_to_value.get(self.return_condition_rating)

        try:
            loan_service.return_loan(loan_id, condition_rating=condition)
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.return_condition_rating = ""
            await self.load_lent_out_books()


__all__ = [
    "LoanActivityState",
    "BorrowedLoanView",
    "LentOutLoanView",
    "LentOutPeriod",
    "LentOutHistoryGroup",
]