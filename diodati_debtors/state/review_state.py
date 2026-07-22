"""Review state — the adapter between Reflex UI and review_service.
Separate from PostState/LibraryState per the bounded-context
discipline established on day two.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import reflex as rx

from ..core.exceptions import DiodatiError
from ..services import review_service, user_service
from .auth_state import AuthState


@dataclass
class ReviewView:
    id: int
    user_name: str
    rating: int
    content: str
    is_own: bool = False


class ReviewState(rx.State):
    reviews: list[ReviewView] = []
    can_review: bool = False
    error_message: str = ""
    info_message: str = ""

    async def load_reviews(self):
        """Populate reviews for the book identified by the route's
        book_id (this page shares the dynamic segment name with the
        book detail page).
        """
        self.error_message = ""
        try:
            bid = int(self.book_id)
        except (TypeError, ValueError, AttributeError):
            self.reviews = []
            return

        auth_state = await self.get_state(AuthState)
        current_user_id = (
            int(auth_state.current_user_id) if auth_state.is_logged_in else None
        )

        try:
            results = review_service.list_reviews_for_book(bid)
            user_results = user_service.list_users()
        except DiodatiError as e:
            self.error_message = str(e)
            return

        names_by_id = {u.id: u.display_name for u in user_results}
        self.reviews = [
            ReviewView(
                id=r.id,
                user_name=names_by_id.get(r.user_id, f"User {r.user_id}"),
                rating=r.rating,
                content=r.content,
                is_own=(r.user_id == current_user_id),
            )
            for r in results
        ]
        # Eligibility check reuses the same rule as review_service —
        # duplicated here only for the UI's "show the form or not"
        # decision; the service remains the final authority (a direct
        # POST would still be validated there regardless).
        self.can_review = current_user_id is not None

    async def submit_review(self, form_data: dict):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to review."
            return
        try:
            bid = int(self.book_id)
            rating = int(form_data.get("rating", "0"))
        except (TypeError, ValueError):
            self.error_message = "Invalid rating."
            return
        try:
            review_service.submit_review(
                book_id=bid,
                user_id=int(auth_state.current_user_id),
                rating=rating,
                content=form_data.get("content", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Review saved."
            await self.load_reviews()

    async def delete_review(self, review_id: int):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            review_service.delete_review(
                int(review_id), user_id=int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            await self.load_reviews()


__all__ = ["ReviewState", "ReviewView"]