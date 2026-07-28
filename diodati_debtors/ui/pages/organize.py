"""Organize page — "What needs my attention?" Two sections: incoming
requests needing a decision, and requests I've sent myself. Once a
sent request has been decided, its response appears as a prominent,
dismissible banner — not just a quiet line in a list — until the
requester explicitly acknowledges it.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button, warning_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.organize_state import (
    JoinRequestView,
    LoanRequestView,
    OrganizeState,
    SentJoinRequestView,
    SentLoanRequestView,
)


def _response_dialog(request_id: int, action_label: str, on_confirm) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            primary_button(action_label, on_click=lambda: OrganizeState.open_response_dialog(request_id))
        ),
        rx.dialog.content(
            rx.dialog.title(f"{action_label}?"),
            rx.vstack(
                rx.input(
                    placeholder="Optional message (e.g. 'Come pick it up after 5pm')",
                    value=OrganizeState.response_message_draft,
                    on_change=OrganizeState.set_response_message_draft,
                ),
                rx.hstack(
                    rx.dialog.close(primary_button("Confirm", on_click=on_confirm)),
                    rx.dialog.close(primary_button("Cancel", type="button")),
                    spacing="2",
                ),
                spacing="3",
            ),
        ),
    )


def _join_request_card(request: JoinRequestView) -> rx.Component:
    return card(
        body_text(f"{request.requester_name} wants to join"),
        meta_text(request.group_name),
        meta_text(f"Requested {request.requested_at}"),
        rx.hstack(
            _response_dialog(request.id, "Approve", lambda: OrganizeState.approve_join(request.id)),
            _response_dialog(request.id, "Decline", lambda: OrganizeState.decline_join(request.id)),
            spacing="3",
            margin_top="0.5rem",
        ),
    )


def _loan_request_card(request: LoanRequestView) -> rx.Component:
    return card(
        body_text(f"{request.requester_name} wants to borrow"),
        meta_text(request.book_title),
        meta_text(f"Requested {request.requested_at}"),
        meta_text(f"Reliability: {request.reliability}"),
        meta_text(f"Book Care: {request.book_care}"),
        rx.cond(request.requested_due_date, meta_text(f"Requested until: {request.requested_due_date}")),
        rx.cond(request.note, meta_text(f"Note: {request.note}")),
        rx.hstack(
            _response_dialog(request.id, "Approve", lambda: OrganizeState.approve_loan(request.id)),
            _response_dialog(request.id, "Decline", lambda: OrganizeState.decline_loan(request.id)),
            spacing="3",
            margin_top="0.5rem",
        ),
    )


def _loan_response_banner(request: SentLoanRequestView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.cond(
                    request.status == "approved",
                    page_title(f"Your request for \"{request.book_title}\" was approved", font_size="1.1rem"),
                    page_title(f"Your request for \"{request.book_title}\" was declined", font_size="1.1rem"),
                ),
                rx.cond(
                    request.response_message,
                    body_text(f"Their reply: \"{request.response_message}\""),
                ),
                spacing="2",
                align="start",
            ),
            warning_button("✕", on_click=lambda: OrganizeState.dismiss_loan_response(request.id), type="button"),
            justify="between",
            width="100%",
            align="start",
        ),
        border=f"2px solid {Color.accent}",
        padding="1rem",
        border_radius="4px",
        margin_bottom="1rem",
    )


def _join_response_banner(request: SentJoinRequestView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.cond(
                    request.status == "approved",
                    page_title(f"Your request to join \"{request.group_name}\" was approved", font_size="1.1rem"),
                    page_title(f"Your request to join \"{request.group_name}\" was declined", font_size="1.1rem"),
                ),
                rx.cond(
                    request.response_message,
                    body_text(f"Their reply: \"{request.response_message}\""),
                ),
                spacing="2",
                align="start",
            ),
            warning_button("✕", on_click=lambda: OrganizeState.dismiss_join_response(request.id), type="button"),
            justify="between",
            width="100%",
            align="start",
        ),
        border=f"2px solid {Color.accent}",
        padding="1rem",
        border_radius="4px",
        margin_bottom="1rem",
    )


def _sent_request_card(request: SentLoanRequestView) -> rx.Component:
    return card(
        body_text(request.book_title),
        meta_text(f"Status: {request.status}"),
        meta_text(f"Requested {request.requested_at}"),
    )


def _sent_join_request_card(request: SentJoinRequestView) -> rx.Component:
    return card(
        body_text(f"Request to join {request.group_name}"),
        meta_text(f"Status: {request.status}"),
        meta_text(f"Requested {request.requested_at}"),
    )


def organize() -> rx.Component:
    return shell(
        page_title("Organize"),
        rx.image(src="/images/organize.jpg", width="100%", margin_bottom="0.5rem"),
        meta_text(
            "Bill from W. Dearden, printer, bookseller, stationer and "
            "bookbinder — Carlton Street, Nottingham, 1830s."
        ),
        divider(),
        rx.cond(
            OrganizeState.error_message != "",
            rx.text(
                OrganizeState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.foreach(
            OrganizeState.sent_requests,
            lambda r: rx.cond(
                (r.status != "pending") & ~r.response_read, _loan_response_banner(r), rx.fragment()
            ),
        ),
        rx.foreach(
            OrganizeState.sent_join_requests,
            lambda r: rx.cond(
                (r.status != "pending") & ~r.response_read, _join_response_banner(r), rx.fragment()
            ),
        ),
        divider(),
        rx.hstack(
            page_title("Pending Join Requests"),
            rx.text(OrganizeState.join_requests.length(), font_family=Font.system, font_size=Type.meta),
            spacing="2", align="center",
        ),
        rx.cond(
            OrganizeState.join_requests.length() > 0,
            rx.grid(
                rx.foreach(OrganizeState.join_requests, _join_request_card),
                columns="repeat(auto-fill, minmax(280px, 1fr))",
                gap="1rem",
                width="100%",
            ),
            body_text("No pending join requests."),
        ),
        divider(),
        rx.hstack(
            page_title("Pending Loan Requests"),
            rx.text(OrganizeState.loan_requests.length(), font_family=Font.system, font_size=Type.meta),
            spacing="2", align="center",
        ),
        rx.cond(
            OrganizeState.loan_requests.length() > 0,
            rx.grid(
                rx.foreach(OrganizeState.loan_requests, _loan_request_card),
                columns="repeat(auto-fill, minmax(280px, 1fr))",
                gap="1rem",
                width="100%",
            ),
            body_text("No pending loan requests."),
        ),
        divider(),
        page_title("Your Pending Requests"),
        rx.grid(
            rx.foreach(
                OrganizeState.sent_requests,
                lambda r: rx.cond(r.status == "pending", _sent_request_card(r), rx.fragment()),
            ),
            columns="repeat(auto-fill, minmax(280px, 1fr))",
            gap="1rem",
            width="100%",
        ),
        rx.grid(
            rx.foreach(
                OrganizeState.sent_join_requests,
                lambda r: rx.cond(r.status == "pending", _sent_join_request_card(r), rx.fragment()),
            ),
            columns="repeat(auto-fill, minmax(280px, 1fr))",
            gap="1rem",
            width="100%",
        ),
        divider(),
        rx.el.details(
            rx.el.summary("☞ Request History", cursor="pointer"),
            rx.grid(
                rx.foreach(
                    OrganizeState.sent_requests,
                    lambda r: rx.cond(r.status != "pending", _sent_request_card(r), rx.fragment()),
                ),
                columns="repeat(auto-fill, minmax(280px, 1fr))",
                gap="1rem",
                width="100%",
            ),
            rx.grid(
                rx.foreach(
                    OrganizeState.sent_join_requests,
                    lambda r: rx.cond(r.status != "pending", _sent_join_request_card(r), rx.fragment()),
                ),
                columns="repeat(auto-fill, minmax(280px, 1fr))",
                gap="1rem",
                width="100%",
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="72rem",
    )


__all__ = ["organize"]