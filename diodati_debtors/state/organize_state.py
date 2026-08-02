"""Organize state — the central inbox for pending decisions the
current user must act on: join requests for clubs they founded, loan
requests for books they own, open Borrowing Inquiries, plus their own
sent requests once decided (shown as a prominent, dismissible
notification until acknowledged).

Per the design notes (project vault): intentionally generic, thinks
in terms of "pending decisions", not "club management" / "book
management" — scales to future request types (invitations,
reservations, ...) without restructuring.

Borrowing Inquiry deliberately lives here, not in Personal Messages
(see Personal Messages Domain Model, project vault, 02.08.): it's
vorgangs-/book-bound, not personen-bound.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import (
    book_service,
    borrowing_inquiry_service,
    group_service,
    loan_service,
    trust_service,
    user_service,
)
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
    response_read: bool = False


@dataclass
class SentJoinRequestView:
    id: int
    group_name: str
    status: str
    requested_at: str
    response_message: str | None = None
    response_read: bool = False


@dataclass
class OpenInquiryView:
    id: int
    book_title: str
    other_person_name: str
    waiting_on_you: bool


class OrganizeState(rx.State):
    join_requests: list[JoinRequestView] = []
    loan_requests: list[LoanRequestView] = []
    sent_requests: list[SentLoanRequestView] = []
    sent_join_requests: list[SentJoinRequestView] = []
    open_inquiries: list[OpenInquiryView] = []
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
            self.open_inquiries = []
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

        try:
            inquiries = borrowing_inquiry_service.list_open_inquiries_for_user(user_id)
        except DiodatiError:
            inquiries = []

        inquiry_views: list[OpenInquiryView] = []
        for inquiry in inquiries:
            other_id = (
                inquiry.owner_id if inquiry.requester_id == user_id else inquiry.requester_id
            )
            try:
                other_name = user_service.get_user(other_id).display_name
            except DiodatiError:
                other_name = f"User {other_id}"
            try:
                book_title = book_service.get_book(inquiry.book_id).title
            except DiodatiError:
                book_title = f"Book {inquiry.book_id}"
            next_user_id = borrowing_inquiry_service.next_to_respond(inquiry)
            inquiry_views.append(
                OpenInquiryView(
                    id=inquiry.id,
                    book_title=book_title,
                    other_person_name=other_name,
                    waiting_on_you=(next_user_id == user_id),
                )
            )
        self.open_inquiries = inquiry_views

        await self.load_sent_requests()
        await self.load_sent_join_requests()

    async def approve_join(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)

        matching_request = next((r for r in self.join_requests if r.id == request_id), None)

        try:
            group_service.approve_join_request(
                request_id, reviewer_id=int(auth_state.current_user_id),
                response_message=self.response_message_draft or None,
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            if matching_request:
                self.info_message = f"Approved {matching_request.requester_name}'s request to join \"{matching_request.group_name}\"."
            else:
                self.info_message = "Join request approved."
            self.pending_response_request_id = 0
            await self.load_all()

    async def decline_join(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)

        matching_request = next((r for r in self.join_requests if r.id == request_id), None)

        try:
            group_service.decline_join_request(
                request_id, reviewer_id=int(auth_state.current_user_id),
                response_message=self.response_message_draft or None,
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            if matching_request:
                self.info_message = f"Declined {matching_request.requester_name}'s request to join \"{matching_request.group_name}\"."
            else:
                self.info_message = "Join request declined."
            self.pending_response_request_id = 0
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
                self.info_message = f"Approved {matching_request.requester_name}'s request for \"{matching_request.book_title}\"."
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
                self.info_message = f"Declined {matching_request.requester_name}'s request for \"{matching_request.book_title}\"."
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
        """Both "decisions I need to make" (as owner/founder) and
        "responses to my own requests I haven't acknowledged yet" —
        one combined number next to "Organize" in the nav. Borrowing
        Inquiries waiting on this user also count.
        """
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.pending_count = 0
            return
        user_id = int(auth_state.current_user_id)
        try:
            join_count = len(group_service.list_pending_join_requests_for_founder(user_id))
            loan_count = len(loan_service.list_pending_loan_requests_for_owner(user_id))
            sent_loan = loan_service.list_loan_requests_for_requester(user_id)
            sent_join = group_service.list_join_requests_for_requester(user_id)
            open_inquiries = borrowing_inquiry_service.list_open_inquiries_for_user(user_id)
        except DiodatiError:
            self.pending_count = 0
            return
        unread_count = sum(
            1 for r in sent_loan if r.status != "pending" and not r.response_read
        ) + sum(
            1 for r in sent_join if r.status != "pending" and not r.response_read
        )
        waiting_on_you_count = sum(
            1 for inquiry in open_inquiries
            if borrowing_inquiry_service.next_to_respond(inquiry) == user_id
        )
        self.pending_count = join_count + loan_count + unread_count + waiting_on_you_count

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
                    response_read=r.response_read,
                )
            )
        self.sent_requests = views

    async def load_sent_join_requests(self):
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.sent_join_requests = []
            return
        try:
            requests = group_service.list_join_requests_for_requester(
                int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        views: list[SentJoinRequestView] = []
        for r in requests:
            try:
                group_name = group_service.get_group(r.group_id).name
            except DiodatiError:
                group_name = f"Club {r.group_id}"
            views.append(
                SentJoinRequestView(
                    id=r.id,
                    group_name=group_name,
                    status=r.status,
                    requested_at=r.requested_at.isoformat(),
                    response_message=r.response_message,
                    response_read=r.response_read,
                )
            )
        self.sent_join_requests = views

    async def dismiss_loan_response(self, request_id: int):
        auth_state = await self.get_state(AuthState)
        try:
            loan_service.mark_loan_request_response_read(
                request_id, requester_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        await self.load_sent_requests()
        await self.load_pending_count()

    async def dismiss_join_response(self, request_id: int):
        auth_state = await self.get_state(AuthState)
        try:
            group_service.mark_join_request_response_read(
                request_id, requester_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return
        await self.load_sent_join_requests()
        await self.load_pending_count()


__all__ = [
    "OrganizeState",
    "JoinRequestView",
    "LoanRequestView",
    "SentLoanRequestView",
    "SentJoinRequestView",
    "OpenInquiryView",
]