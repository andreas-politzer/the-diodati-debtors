"""Post state — the adapter between Reflex UI and post_service/
comment_service. Covers all three projections (Global Board, Club
Feed, Book Discussion) — same underlying shape, different source
query, per the Communication Domain Model.

PostView/CommentView are typed dataclasses, not dicts — nested lists
(comments per post) need explicit typing for rx.foreach, per the
lesson learned earlier in this project.

Separate from LibraryState/GroupState/OrganizeState per the bounded-
context discipline established on day two.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import comment_service, post_service, user_service
from .auth_state import AuthState
from .group_state import GroupState


@dataclass
class CommentView:
    id: int
    author_name: str
    content: str
    is_own: bool = False


@dataclass
class PostView:
    id: int
    author_name: str
    content: str
    post_type: str
    is_own: bool = False
    comments: list[CommentView] = field(default_factory=list)


class PostState(rx.State):
    board_posts: list[PostView] = []
    club_posts: list[PostView] = []
    book_posts: list[PostView] = []
    error_message: str = ""
    info_message: str = ""

    async def _build_post_views(self, post_results) -> list[PostView]:
        """Shared enrichment: author name, ownership, and comments per
        post. One user_service call total, then per-post comment
        lookups (acceptable at this scale — same reasoning as the book
        detail page's loan history).
        """
        auth_state = await self.get_state(AuthState)
        current_user_id = (
            int(auth_state.current_user_id) if auth_state.is_logged_in else None
        )

        try:
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return []
        names_by_id = {u.id: u.display_name for u in user_results}

        views: list[PostView] = []
        for post in post_results:
            try:
                comment_results = comment_service.list_comments_for_post(post.id)
            except DiodatiError:
                comment_results = []

            comments = [
                CommentView(
                    id=c.id,
                    author_name=names_by_id.get(c.author_id, f"User {c.author_id}"),
                    content=c.content,
                    is_own=(c.author_id == current_user_id),
                )
                for c in comment_results
            ]

            views.append(
                PostView(
                    id=post.id,
                    author_name=names_by_id.get(post.author_id, f"User {post.author_id}"),
                    content=post.content,
                    post_type=post.post_type,
                    is_own=(post.author_id == current_user_id),
                    comments=comments,
                )
            )
        return views

    async def load_board(self):
        self.error_message = ""
        try:
            results = post_service.list_global_board_posts()
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.board_posts = await self._build_post_views(results)

    async def load_club_feed(self):
        self.error_message = ""
        group_state = await self.get_state(GroupState)
        if not group_state.current_group_id:
            self.club_posts = []
            return
        try:
            results = post_service.list_club_feed_posts(int(group_state.current_group_id))
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.club_posts = await self._build_post_views(results)

    async def load_book_discussion(self):
        self.error_message = ""
        try:
            bid = int(self.book_id)
        except (TypeError, ValueError, AttributeError):
            # No book_id in this route's context — e.g. called from
            # submit_comment's "refresh everything" on a page that
            # isn't the book detail page. Not an error here.
            self.book_posts = []
            return
        try:
            results = post_service.list_book_discussion_posts(bid)
        except DiodatiError as e:
            self.error_message = str(e)
            return
        self.book_posts = await self._build_post_views(results)

    async def submit_board_post(self, form_data: dict):
        await self._submit_post(form_data, group_id=None, book_id=None)
        await self.load_board()

    async def submit_club_post(self, form_data: dict):
        group_state = await self.get_state(GroupState)
        if not group_state.current_group_id:
            self.error_message = "Select a club first."
            return
        await self._submit_post(
            form_data, group_id=int(group_state.current_group_id), book_id=None
        )
        await self.load_club_feed()

    async def submit_book_discussion_post(self, form_data: dict):
        try:
            bid = int(self.book_id)
        except (TypeError, ValueError):
            self.error_message = "Invalid book id."
            return
        await self._submit_post(form_data, group_id=None, book_id=bid)
        await self.load_book_discussion()

    async def _submit_post(self, form_data: dict, group_id: int | None, book_id: int | None):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to post."
            return
        try:
            post_service.create_post(
                author_id=int(auth_state.current_user_id),
                content=form_data.get("content", ""),
                group_id=group_id,
                book_id=book_id,
                post_type=form_data.get("post_type", "general"),
            )
        except DiodatiError as e:
            self.error_message = str(e)

    async def submit_comment(self, form_data: dict):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to comment."
            return
        try:
            post_id = int(form_data.get("post_id", ""))
        except (TypeError, ValueError):
            self.error_message = "Invalid post."
            return
        try:
            comment_service.create_comment(
                post_id=post_id,
                author_id=int(auth_state.current_user_id),
                content=form_data.get("content", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_board()
            await self.load_club_feed()
            await self.load_book_discussion()

    async def delete_post(self, post_id: int):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            post_service.delete_post(int(post_id), author_id=int(auth_state.current_user_id))
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_board()
            await self.load_club_feed()
            await self.load_book_discussion()

    async def delete_comment(self, comment_id: int):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            comment_service.delete_comment(
                int(comment_id), author_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_board()
            await self.load_club_feed()
            await self.load_book_discussion()


__all__ = ["PostState", "PostView", "CommentView"]