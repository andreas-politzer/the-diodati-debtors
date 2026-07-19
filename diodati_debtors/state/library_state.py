"""Library state — the adapter between Reflex UI and the service layer.

Per the Architecture Contract: State is orchestration, not business
logic. Service decides whether an action is allowed; State decides
when to call the service and translates results/errors into UI-facing
state; UI only renders state and triggers events.

This class never imports SQLAlchemy or touches models directly — only
services/. State depends on each service's explicit .to_dict() method,
never on dataclasses.asdict() directly — the service owns its own
serialization, so its internal representation can evolve without
breaking this file.
"""

from __future__ import annotations

import datetime as dt

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import book_service, loan_service, user_service


class LibraryState(rx.State):
    books: list[dict] = []
    users: list[dict] = []
    error_message: str = ""

    def load_books(self) -> None:
        """Fetch all books plus their loan status in two service calls
        total (not one per book — see get_active_loans_for_books).
        """
        self.error_message = ""
        try:
            book_results = book_service.list_books()
        except DiodatiError as e:
            self.error_message = str(e)
            return

        book_ids = [b.id for b in book_results]
        active_loans = loan_service.get_active_loans_for_books(book_ids)

        enriched: list[dict] = []
        for book in book_results:
            entry = book.to_dict()
            active_loan = active_loans.get(book.id)
            entry["status"] = "on loan" if active_loan else "available"
            entry["active_loan_id"] = active_loan.id if active_loan else None
            entry["borrower_id"] = active_loan.borrower_id if active_loan else None
            enriched.append(entry)
        self.books = enriched

    def load_users(self) -> None:
        """Fetch all users, for the borrower picker."""
        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.users = [u.to_dict() for u in user_results]

    def load_all(self) -> None:
        self.load_books()
        self.load_users()

    def lend_book(self, book_id: int, borrower_id: int, due_in_days: int = 14) -> None:
        """Attempt to lend a book. Domain exceptions are translated into
        error_message here — never allowed to escape to Reflex's default
        error boundary.
        """
        self.error_message = ""
        try:
            loan_service.create_loan(
                book_id=book_id,
                borrower_id=borrower_id,
                due_date=dt.date.today() + dt.timedelta(days=due_in_days),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.load_books()

    def return_book(self, loan_id: int) -> None:
        """Attempt to return a loan. Same exception-translation pattern
        as lend_book.
        """
        self.error_message = ""
        try:
            loan_service.return_loan(loan_id)
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.load_books()


__all__ = ["LibraryState"]