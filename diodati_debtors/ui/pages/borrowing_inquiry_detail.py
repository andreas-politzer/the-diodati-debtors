"""Borrowing Inquiry Detail — complete message history for one
book-bound Public Borrowing Inquiry, with reply and close actions.
Compact single-line message rows, same visual language as Club
Conversation Detail.
"""

from __future__ import annotations

import reflex as rx

from ..components.avatar import avatar
from ..components.button import primary_button, warning_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.borrowing_inquiry_detail_state import BorrowingInquiryDetailState, InquiryMessageView


def _message_row(message: InquiryMessageView) -> rx.Component:
    return rx.hstack(
        avatar(message.sender_monogram, size="24px"),
        rx.vstack(
            rx.hstack(
                meta_text(message.sender_display_name, font_weight="600"),
                meta_text(message.sent_at),
                spacing="2",
            ),
            body_text(message.content),
            spacing="0",
            align="start",
        ),
        spacing="2",
        align="start",
        padding_y="0.4rem",
        border_bottom="1px solid #ddd",
    )


def borrowing_inquiry_detail() -> rx.Component:
    return shell(
        page_title(f"Re: {BorrowingInquiryDetailState.book_title}"),
        meta_text(f"With {BorrowingInquiryDetailState.other_person_name}"),
        rx.cond(
            BorrowingInquiryDetailState.error_message != "",
            rx.text(BorrowingInquiryDetailState.error_message, color="red"),
        ),
        rx.cond(
            BorrowingInquiryDetailState.info_message != "",
            meta_text(BorrowingInquiryDetailState.info_message),
        ),
        rx.foreach(BorrowingInquiryDetailState.messages, _message_row),
        divider(),
        rx.cond(
            BorrowingInquiryDetailState.status == "open",
            rx.vstack(
                rx.form(
                    rx.vstack(
                        rx.text_area(
                            placeholder="Continue the conversation...",
                            value=BorrowingInquiryDetailState.reply_draft,
                            on_change=BorrowingInquiryDetailState.set_reply_draft,
                            rows="3",
                        ),
                        primary_button("Send", type="submit"),
                        spacing="3",
                    ),
                    on_submit=BorrowingInquiryDetailState.send_reply,
                ),
                warning_button("Close this inquiry", on_click=BorrowingInquiryDetailState.close, margin_top="1rem"),
                spacing="3",
                width="100%",
            ),
            meta_text("This inquiry is closed."),
        ),
        rx.link("☞ Back to Organize", href="/organize", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["borrowing_inquiry_detail"]