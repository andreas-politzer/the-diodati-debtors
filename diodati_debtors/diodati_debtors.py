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
app.add_page(landing, route="/")
app.add_page(style_preview, route="/style-preview")
app.add_page(login, route="/login", on_load=AuthState.redirect_if_logged_in)
app.add_page(register, route="/register", on_load=AuthState.redirect_if_logged_in)
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
    book_detail,
    route="/book/[book_id]",
    on_load=[AuthState.check_auth, LibraryState.load_book_detail],
)
app.add_page(
    add_book,
    route="/add-book",
    on_load=[AuthState.check_auth, LibraryState.load_users],
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