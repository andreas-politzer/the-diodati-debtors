"""Organize page — central inbox for pending decisions: join requests
for clubs I founded, loan requests for books I own. One shared card
layout for both request types per the design notes (project vault) —
intentionally generic, not "club management" / "book management".
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button, warning_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.organize_state import JoinRequestView, LoanRequestView, OrganizeState


def _request_card(title_text: str, subtitle: str, requested_at: str, on_approve, on_decline) -> rx.Component:
    return card(
        body_text(title_text),
        meta_text(subtitle),
        meta_text(f"Requested {requested_at}"),
        rx.hstack(
            primary_button("Approve", on_click=on_approve),
            warning_button("Decline", on_click=on_decline),
            spacing="3",
            margin_top="0.5rem",
        ),
        margin_bottom="1rem",
    )


def _join_request_card(request: JoinRequestView) -> rx.Component:
    return _request_card(
        title_text=f"{request.requester_name} wants to join",
        subtitle=request.group_name,
        requested_at=request.requested_at,
        on_approve=lambda: OrganizeState.approve_join(request.id),
        on_decline=lambda: OrganizeState.decline_join(request.id),
    )


def _loan_request_card(request: LoanRequestView) -> rx.Component:
    return _request_card(
        title_text=f"{request.requester_name} wants to borrow",
        subtitle=request.book_title,
        requested_at=request.requested_at,
        on_approve=lambda: OrganizeState.approve_loan(request.id),
        on_decline=lambda: OrganizeState.decline_loan(request.id),
    )


def organize() -> rx.Component:
    return shell(
        page_title("Organize"),
        rx.cond(
            OrganizeState.error_message != "",
            rx.text(
                OrganizeState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            OrganizeState.info_message != "",
            meta_text(OrganizeState.info_message),
        ),
        divider(),
        rx.hstack(
            page_title("Pending Join Requests"),
            rx.text(
                OrganizeState.join_requests.length(),
                font_family=Font.system,
                font_size=Type.meta,
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            OrganizeState.join_requests.length() > 0,
            rx.foreach(OrganizeState.join_requests, _join_request_card),
            body_text("No pending join requests."),
        ),
        divider(),
        rx.hstack(
            page_title("Pending Loan Requests"),
            rx.text(
                OrganizeState.loan_requests.length(),
                font_family=Font.system,
                font_size=Type.meta,
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            OrganizeState.loan_requests.length() > 0,
            rx.foreach(OrganizeState.loan_requests, _loan_request_card),
            body_text("No pending loan requests."),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["organize"]