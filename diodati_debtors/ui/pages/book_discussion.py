"""Book Discussion — one projection of the shared Post entity: posts
where book_id equals this specific book. Visibility follows the same
rule as the book itself (owner + members of any club the owner
belongs to), enforced by post_service, not duplicated here.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.community_guidelines import community_guidelines
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.post_state import CommentView, PostState, PostView


def _comment_row(comment: CommentView) -> rx.Component:
    return rx.hstack(
        meta_text(comment.author_name),
        body_text(comment.content),
        rx.cond(
            comment.is_own,
            primary_button("Delete", on_click=lambda: PostState.delete_comment(comment.id)),
        ),
        spacing="2",
        margin_bottom="0.25rem",
    )


def _post_card(post: PostView) -> rx.Component:
    return card(
        meta_text(post.author_name),
        body_text(post.content),
        rx.cond(
            post.is_own,
            primary_button("Delete", on_click=lambda: PostState.delete_post(post.id)),
        ),
        divider(),
        rx.foreach(post.comments, _comment_row),
        rx.form(
            rx.hstack(
                rx.input(name="post_id", value=post.id, type="hidden"),
                rx.input(placeholder="Write a comment...", name="content"),
                primary_button("Reply", type="submit"),
                spacing="2",
            ),
            on_submit=PostState.submit_comment,
            reset_on_submit=True,
        ),
        margin_bottom="1rem",
    )


def book_discussion() -> rx.Component:
    return shell(
        page_title("Discussion"),
        rx.cond(
            PostState.error_message != "",
            rx.text(
                PostState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        community_guidelines(),
        rx.form(
            rx.vstack(
                rx.text_area(placeholder="Ask something about this book...", name="content", rows="3"),
                primary_button("Post", type="submit"),
                spacing="3",
            ),
            on_submit=PostState.submit_book_discussion_post,
            reset_on_submit=True,
        ),
        divider(),
        rx.cond(
            PostState.book_posts.length() > 0,
            rx.foreach(PostState.book_posts, _post_card),
            body_text("No discussion yet for this book."),
        ),
        rx.link(
            "☞ Back to book", href=f"/book/{PostState.book_id}", margin_top="1rem", display="block"
        ),
        max_width="40rem",
    )


__all__ = ["book_discussion"]