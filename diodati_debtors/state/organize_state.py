"""Organize state — the central inbox for pending decisions the
current user must act on: join requests for clubs they founded, loan
requests for books they own.

Per the design notes (project vault): intentionally generic, thinks
in terms of "pending decisions", not "club management" / "book
management" — scales to future request types (invitations,
reservations, ...) without restructuring.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import book_service, group_service, loan_service, trust_service, user_service
from .auth_state import AuthState


@dataclass
class JoinRequestView:
    id: int
    requester_name: str
    group_name: str
    requested_at: str

@dataclass
class LoanRequestView:
    id: int
    requester_name: str
    book_title: str
    requested_at: str
    reliability: str = ""
    book_care: str = ""
    requested_due_date: str | None = None
    note: str | None = None

@dataclass
class SentLoanRequestView:
    id: int
    book_title: str
    status: str
    requested_at: str
    response_message: str | None = None


class OrganizeState(rx.State):
    join_requests: list[JoinRequestView] = []
    loan_requests: list[LoanRequestView] = []
    sent_requests: list[SentLoanRequestView] = []
    error_message: str = ""
    info_message: str = ""
    pending_response_request_id: int = 0
    response_message_draft: str = ""
    pending_count: int = 0

    async def load_all(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.join_requests = []
            self.loan_requests = []
            return
        user_id = int(auth_state.current_user_id)

        try:
            join_reqs = group_service.list_pending_join_requests_for_founder(user_id)
            loan_reqs = loan_service.list_pending_loan_requests_for_owner(user_id)
        except DiodatiError as e:
            self.error_message = str(e)
            return

        join_views: list[JoinRequestView] = []
        for r in join_reqs:
            try:
                requester_name = user_service.get_user(r.user_id).display_name
                group_name = group_service.get_group(r.group_id).name
            except DiodatiError:
                requester_name = f"User {r.user_id}"
                group_name = f"Group {r.group_id}"
            join_views.append(
                JoinRequestView(
                    id=r.id,
                    requester_name=requester_name,
                    group_name=group_name,
                    requested_at=r.requested_at.isoformat(),
                )
            )
        self.join_requests = join_views

        loan_views: list[LoanRequestView] = []
        for r in loan_reqs:
            try:
                requester_name = user_service.get_user(r.requester_id).display_name
                book_title = book_service.get_book(r.book_id).title
            except DiodatiError:
                requester_name = f"User {r.requester_id}"
                book_title = f"Book {r.book_id}"
            signals = trust_service.get_trust_signals(r.requester_id)
            loan_views.append(
                LoanRequestView(
                    id=r.id,
                    requester_name=requester_name,
                    book_title=book_title,
                    requested_at=r.requested_at.isoformat(),
                    reliability=signals.reliability,
                    book_care=signals.book_care,
                    requested_due_date=r.requested_due_date.isoformat() if r.requested_due_date else None,
                    note=r.note,
                )
            )
        self.loan_requests = loan_views
        await self.load_sent_requests()

    async def approve_join(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            group_service.approve_join_request(
                request_id, reviewer_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Join request approved."
            await self.load_all()

    async def decline_join(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            group_service.decline_join_request(
                request_id, reviewer_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Join request declined."
            await self.load_all()

    async def approve_loan(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)

        matching_request = next((r for r in self.loan_requests if r.id == request_id), None)

        try:
            loan_service.approve_loan_request(
                request_id, reviewer_id=int(auth_state.current_user_id),
                response_message=self.response_message_draft or None,
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            if matching_request:
                self.info_message = (
                    f"Approved {matching_request.requester_name}'s request for "
                    f"\"{matching_request.book_title}\"."
                    + (f" Your reply: \"{self.response_message_draft}\"" if self.response_message_draft else "")
                )
            else:
                self.info_message = "Loan request approved."
            self.pending_response_request_id = 0
            await self.load_all()

    async def decline_loan(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)

        matching_request = next((r for r in self.loan_requests if r.id == request_id), None)

        try:
            loan_service.decline_loan_request(
                request_id, reviewer_id=int(auth_state.current_user_id),
                response_message=self.response_message_draft or None,
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            if matching_request:
                self.info_message = (
                    f"Declined {matching_request.requester_name}'s request for "
                    f"\"{matching_request.book_title}\"."
                    + (f" Your reply: \"{self.response_message_draft}\"" if self.response_message_draft else "")
                )
            else:
                self.info_message = "Loan request declined."
            self.pending_response_request_id = 0
            await self.load_all()

    def open_response_dialog(self, request_id: int):
        self.pending_response_request_id = request_id
        self.response_message_draft = ""

    def cancel_response_dialog(self):
        self.pending_response_request_id = 0

    def set_response_message_draft(self, value: str):
        self.response_message_draft = value

    async def load_pending_count(self):
        """Lightweight — just the count, no name/trust enrichment.
        Used by the Dashboard nav badge, separate from load_all()
        (which does the full Organize page's enrichment)."""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.pending_count = 0
            return
        user_id = int(auth_state.current_user_id)
        try:
            join_count = len(group_service.list_pending_join_requests_for_founder(user_id))
            loan_count = len(loan_service.list_pending_loan_requests_for_owner(user_id))
        except DiodatiError:
            self.pending_count = 0
            return
        self.pending_count = join_count + loan_count

    async def load_sent_requests(self):
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.sent_requests = []
            return
        try:
            requests = loan_service.list_loan_requests_for_requester(
                int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        views: list[SentLoanRequestView] = []
        for r in requests:
            try:
                book_title = book_service.get_book(r.book_id).title
            except DiodatiError:
                book_title = f"Book {r.book_id}"
            views.append(
                SentLoanRequestView(
                    id=r.id,
                    book_title=book_title,
                    status=r.status,
                    requested_at=r.requested_at.isoformat(),
                    response_message=r.response_message,
                )
            )
        self.sent_requests = views


__all__ = ["OrganizeState", "JoinRequestView", "LoanRequestView", "SentLoanRequestView"]