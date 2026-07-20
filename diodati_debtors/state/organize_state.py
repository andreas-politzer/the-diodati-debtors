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
from ..services import book_service, group_service, loan_service, user_service
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


class OrganizeState(rx.State):
    join_requests: list[JoinRequestView] = []
    loan_requests: list[LoanRequestView] = []
    error_message: str = ""
    info_message: str = ""

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
            loan_views.append(
                LoanRequestView(
                    id=r.id,
                    requester_name=requester_name,
                    book_title=book_title,
                    requested_at=r.requested_at.isoformat(),
                )
            )
        self.loan_requests = loan_views

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
        try:
            loan_service.approve_loan_request(
                request_id, reviewer_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Loan request approved."
            await self.load_all()

    async def decline_loan(self, request_id: int):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            loan_service.decline_loan_request(
                request_id, reviewer_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Loan request declined."
            await self.load_all()


__all__ = ["OrganizeState", "JoinRequestView", "LoanRequestView"]