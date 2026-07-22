"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from .ui.theme import global_style, stylesheets
from .ui.pages.style_preview import style_preview
from .ui.pages.landing import landing
from .ui.pages.login import login
from .ui.pages.register import register
from .ui.pages.clubs import clubs
from .ui.pages.dashboard import dashboard
from .ui.pages.book_detail import book_detail
from .ui.pages.add_book import add_book
from .ui.pages.organize import organize
from .ui.pages.members import members
from .ui.pages.member_detail import member_detail
from .ui.pages.edit_book import edit_book
from .ui.pages.imprint import imprint
from .ui.pages.privacy import privacy
from .ui.pages.club_feed import club_feed
from .ui.pages.global_board import global_board
from .ui.pages.reviews import reviews
from .ui.pages.synopsis import synopsis
from .state.review_state import ReviewState
from .state.post_state import PostState
from .state.auth_state import AuthState
from .state.group_state import GroupState
from .state.library_state import LibraryState
from .state.organize_state import OrganizeState


class State(rx.State):
    """The app state."""


app = rx.App(
    style=global_style(),
    stylesheets=stylesheets(),
)
app.add_page(
    landing,
    route="/",
    title="The Diodati Debtors | Community Library for Book Clubs",
    description=(
        "A community library application for book clubs. "
        "Catalogue your books, lend and borrow within your club, "
        "and keep track of shared libraries."
    ),
    meta=[
        {
            "property": "og:title",
            "content": "The Diodati Debtors | Community Library for Book Clubs",
        },
        {
            "property": "og:description",
            "content": (
                "A community library application for book clubs. "
                "Catalogue your books, lend and borrow within your club, "
                "and keep track of shared libraries."
            ),
        },
        {
            "property": "og:type",
            "content": "website",
        },
    ],
)
app.add_page(style_preview, route="/style-preview")
app.add_page(login, route="/login", on_load=AuthState.redirect_if_logged_in)
app.add_page(register, route="/register", on_load=AuthState.redirect_if_logged_in)
app.add_page(
    imprint,
    route="/imprint",
    title="Imprint | The Diodati Debtors",
    description="Legal notice and provider information for The Diodati Debtors.",
)

app.add_page(
    privacy,
    route="/privacy",
    title="Privacy Policy | The Diodati Debtors",
    description=(
        "Information about how The Diodati Debtors processes and protects personal data."
    ),
)
app.add_page(
    clubs,
    route="/clubs",
    on_load=[AuthState.check_auth, GroupState.load_all],
)
app.add_page(
    dashboard,
    route="/dashboard",
    on_load=[AuthState.check_auth, GroupState.load_my_groups, LibraryState.load_all],
)
app.add_page(
    global_board,
    route="/board",
    on_load=[AuthState.check_auth, PostState.load_board],
)
app.add_page(
    book_detail,
    route="/book/[book_id]",
    on_load=[AuthState.check_auth, LibraryState.load_book_detail],
)
app.add_page(
    add_book,
    route="/add-book",
    on_load=[AuthState.check_auth, LibraryState.reset_form_fields],
)
app.add_page(
    organize,
    route="/organize",
    on_load=[AuthState.check_auth, OrganizeState.load_all],
)
app.add_page(
    members,
    route="/members",
    on_load=[AuthState.check_auth, GroupState.load_my_groups, GroupState.load_members_overview],
)
app.add_page(
    member_detail,
    route="/members/[member_id]",
    on_load=[AuthState.check_auth, LibraryState.load_member_library],
)
app.add_page(
    edit_book,
    route="/book/[book_id]/edit",
    on_load=[AuthState.check_auth, LibraryState.load_book_detail],
)
app.add_page(
    club_feed,
    route="/club-feed",
    on_load=[AuthState.check_auth, PostState.load_club_feed],
)
app.add_page(
    reviews,
    route="/book/[book_id]/reviews",
    on_load=[AuthState.check_auth, ReviewState.load_reviews],
)
app.add_page(
    synopsis,
    route="/book/[book_id]/synopsis",
    on_load=[AuthState.check_auth, LibraryState.load_book_detail],
)