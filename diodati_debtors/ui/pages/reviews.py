"""Reviews page — own route (not nested in book detail) to avoid the
scroll-monster problem Andy flagged: a long loan history would push
reviews out of sight otherwise. Linked from the book detail header.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button, warning_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.review_state import ReviewState, ReviewView


def _review_card(review: ReviewView) -> rx.Component:
    return card(
        meta_text(review.user_name),
        rx.match(
            review.rating,
            (1, rx.text("🦉", font_size="1.2rem")),
            (2, rx.text("🦉🦉", font_size="1.2rem")),
            (3, rx.text("🦉🦉🦉", font_size="1.2rem")),
            (4, rx.text("🦉🦉🦉🦉", font_size="1.2rem")),
            (5, rx.text("🦉🦉🦉🦉🦉", font_size="1.2rem")),
            rx.text("", font_size="1.2rem"),
        ),
        body_text(review.content),
        rx.cond(
            review.is_own,
            warning_button("Delete", on_click=lambda: ReviewState.delete_review(review.id)),
        ),
        margin_bottom="1rem",
    )


def reviews() -> rx.Component:
    return shell(
        page_title("Reviews"),
        rx.cond(
            ReviewState.error_message != "",
            rx.text(
                ReviewState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            ReviewState.info_message != "",
            meta_text(ReviewState.info_message),
        ),
        meta_text(
            "Only the book's owner or someone who has borrowed it may "
            "write a review."
        ),
        rx.form(
            rx.vstack(
                rx.select(["1", "2", "3", "4", "5"], name="rating", placeholder="Owls (1-5)"),
                rx.text_area(placeholder="Your review...", name="content", rows="3"),
                primary_button("Submit review", type="submit"),
                spacing="3",
            ),
            on_submit=ReviewState.submit_review,
            reset_on_submit=True,
        ),
        divider(),
        rx.cond(
            ReviewState.reviews.length() > 0,
            rx.foreach(ReviewState.reviews, _review_card),
            body_text("No reviews yet."),
        ),
        rx.link(
            "☞ Back to book", href=f"/book/{ReviewState.book_id}", margin_top="1rem", display="block"
        ),
        max_width="40rem",
    )


__all__ = ["reviews"]