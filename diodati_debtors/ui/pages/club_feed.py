"""Club Feed page — one projection of the shared Post entity (see
Communication Domain Model, project vault): posts where group_id
equals the currently selected club.

post_type is purely presentational: the raven (☝ raven glyph) marks
Announcements, general/question posts show no extra glyph — the
Manicule/Vanitas-motif discipline (rare, meaningful accents, never a
symbol for every single state) applies here too.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.group_state import GroupState
from ...state.post_state import CommentView, PostState, PostView


def _comment_row(comment: CommentView) -> rx.Component:
    return rx.hstack(
        meta_text(comment.author_name),
        body_text(comment.content),
        rx.cond(
            comment.is_own,
            primary_button(
                "Delete", on_click=lambda: PostState.delete_comment(comment.id)
            ),
        ),
        spacing="2",
        margin_bottom="0.25rem",
    )


def _post_card(post: PostView) -> rx.Component:
    return card(
        rx.hstack(
            meta_text(post.author_name),
            rx.cond(post.post_type == "announcement", rx.text("𓅃", font_size="1.2rem")),
            spacing="2",
        ),
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


def club_feed() -> rx.Component:
    return shell(
        page_title("Club Feed"),
        meta_text(GroupState.current_group_name),
        rx.cond(
            PostState.error_message != "",
            rx.text(
                PostState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            GroupState.current_group_id == "",
            rx.fragment(
                body_text("Select a club first."),
                rx.link("☞ Go to your clubs", href="/dashboard", margin_top="0.5rem", display="block"),
            ),
            rx.fragment(
                rx.form(
                    rx.vstack(
                        rx.text_area(placeholder="What's on your mind?", name="content", rows="3"),
                        
                        primary_button("Post", type="submit"),
                        spacing="3",
                    ),
                    on_submit=PostState.submit_club_post,
                    reset_on_submit=True,
                ),
                divider(),
                rx.cond(
                    PostState.club_posts.length() > 0,
                    rx.foreach(PostState.club_posts, _post_card),
                    body_text("No posts yet in this club."),
                ),
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["club_feed"]
